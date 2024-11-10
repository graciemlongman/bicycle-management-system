
from database import *

from datetime import date, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import collections
import numpy as np
import ipywidgets as widgets

import membershipManager as m

class BikeSelect():
    '''
    Class containing functions that allow the store manage to choose bikes 
    to maintain or expand inventory. Based on popularity, age and condition.
    Has trend visualisation functionality

    Notes: every bike in the inventory table has a unique bicycle id AND a 
    non-unique model id, which is the foreign key to the models table, and which
    describes the non-variable attributes of the bike model such as brand/type/
    size.

    FUNCTIONS:
    - select(self, database, allocation, budget) -> df
        To expand the current inventory:
            Every bike in the inventory is assigned an overall score based on 
            age, popularity and condition. The closer to 100, the more likely it
            will be to get replaced.
            The top ten bikes are then chosen, and the algorithm selects bikes 
            from this list within the budget.

        To choose new bikes:
            The bikes are chosen from the model dataframe if they are not in the 
            current inventory.
        
        Budget allocation can be adjusted based on user's priority for replacing
        bikes or buying new ones.

    - visualise

    HELPER FUNCTIONS:
    - _assign_score(self) -> 2D list

    - _sort_by_score_and_get_model_id(self, id_and_scores) -> list

    - _select_bikes(self, budget, model_ids) -> df

    '''

    def __init__(self, database):
        '''
        '''
        #read in datatables
        self.conn = database.connection
        self.bicycle_models = pd.read_sql('SELECT * FROM bicycle_models', self.conn, index_col=['model_id'])
        self.inventory = pd.read_sql('SELECT * FROM bicycle_inventory', self.conn, index_col=['id'])
        self.history = pd.read_sql('SELECT * FROM rental_hist', self.conn, index_col=['id'] )
        self.images = pd.read_sql('SELECT * FROM images', self.conn, index_col=['brand'])
    
    def select(self, allocation, budget):
        '''
        Overall select function (see above)
        Args:
        -------
        database:
        allocation (int):
        budget (int):

        Returns:
        ----------
        Confirmation message
        Dataframe of bikes that should be selected for purchase
        Pd series of image blobs
        '''
        self.budget = budget

        #calculate overall score for each bicycle in inventory
        id_and_scores = self._assign_score()
  
        #sorted by score with highest first, older, damaged bikes more likely to be replaced
        top10_models = self._sort_by_score_and_get_model_id(id_and_scores)

        #inventory will be maintained up to budget allocation
        maintain_budget = (allocation/100) * self.budget
        maintain_df = self._select_bikes(budget=maintain_budget, model_ids = top10_models)

        #after budget has been allocated, rest goes to new bikes
        new_bike_budget = self.budget - maintain_budget
        new_models = self.bicycle_models[self.bicycle_models['instore'] == 'no']

        new_df = self._select_bikes(budget=new_bike_budget, model_ids = [x for x in new_models.index])
        
        overall_selected_df = pd.concat([maintain_df, new_df])
        brands = overall_selected_df.groupby('brand').size()
        images = self.images[self.images.index.isin(brands.index)]

        confirmation_message = widgets.HTML(value=f"<h3>Overall budget was £{self.budget}, with {allocation}% of the budget allocated to maintaining the current inventory</h3>")
        return confirmation_message, overall_selected_df, images

    def visualise(self):
        '''
        Visualise rental frequency of bicycles
        Returns:
        ---------
        matplotlib figure
        '''
        #get the matching model id to each each bike id in the history table
        matched_model_ids = self.inventory['model_id'].reindex(self.history.index)

        #add as a col to the history table
        self.history['model_id'] = matched_model_ids

        # get the sum of each rent by each member for each model
        grouped = self.history.groupby(['member_id', 'model_id']).size().unstack(fill_value=0)
        
        #plot
        fig, ax = plt.subplots(figsize=(15,15))

        im = ax.imshow(grouped, cmap ='YlGnBu')

        cbar = ax.figure.colorbar(im,ax=ax, fraction=0.02, pad=0.04)
        cbar.set_label('Frequency of Usage')

        ax.set_title('Rental frequency of bikes since 2021, by member and model', fontsize=20)
        ax.set_xlabel('Model ID - corresponds to each unique bike (not to be confused with bicycle ID, which corresponds to each actual bike in the inventory)', 
                      fontsize=12)
        ax.set_ylabel('Member ID', fontsize = 12)
        
        ax.set_xticks(range(len(grouped.columns)))
        ax.set_xticklabels(grouped.columns)
        
        ax.set_yticks(range(len(grouped.index)))
        ax.set_yticklabels(grouped.index)

        fig.tight_layout()
        plt.show()
        
    
    ##############################################################
            ## Helper methods
    ##############################################################

    def _assign_score(self):
        '''
        Algorithm which assigns a score to each model bike, from 0 to 100
        The higher the score, the more likely it should be selected
        Bikes that are popular, old or damaged get a higher score.
        Returns:
        ----------
        list of bike ids and corresponding score in the format
        [   [bike_id, score],
            [bike_id, score],
        ....[bike_id, score]]

        '''
        
        total_count = len(self.history)
        cutoff_age = 10*365

        scores = []
        for b_id in self.inventory.index:
            bike_id = b_id-1 #0 order indexing

            popularity = self.history.iloc[bike_id].count()
            popularity_score = popularity/total_count if total_count>0 else 0 
            
            age = self.inventory['purchase_date'].iloc[bike_id]
            age_days = (date.today()-age).days
            age_score = min(age_days/cutoff_age, 1)

            condition = self.inventory['condition'].iloc[bike_id]
            condition_score = 1 if condition == 'Damaged' else 0
            
            score = (popularity_score + age_score + condition_score)*100/3
            scores.append((bike_id,score))

        return scores

    def _sort_by_score_and_get_model_id(self, id_and_scores):
        '''
        Sort bikes by highest score first, select top 10.
        Return the model id of each bike to be replaced
        Args:
        -------
        id_and_scores (2D list):
        '''
        #get top10, sorted by highest score first
        top10 = sorted(id_and_scores, key=lambda x:x[1], reverse=True)[0:10]
        
        #make 1D - take the bicycle id out only
        top10_bike_ids = [id[0]-1 for id in top10] #0 order indexing

        #get the model id of each bike in the list
        return self.inventory['model_id'].iloc[top10_bike_ids]

    def _select_bikes(self, budget, model_ids):
        '''
        Selects and returns a DataFrame of bicycle models within a specified 
        budget. The function iterates over the list of model IDs and adds to 
        the selection as long as the budget is not exceeded. Each model has a 
        maximum allowed quantity proportional to its cost relative to the budget
        to prevent overselection.

        Parameters:
        -----------
        budget (int): The maximum total cost allowed for the selected bikes.
            
        model_ids (list of int): A list of the top 10 models needed to be 
        replaced in the case of mainting inventory, or a list of all models that
        the store does not own in the case of expanding the inventory.

        Returns:
        --------
        model_df : DataFrame
            A DataFrame containing the selected bikes within the budget.
            Each row represents a unique bike model.
        '''
        bikes_selected = []
        total_cost = 0
        bike_count = {m_id: 0 for m_id in model_ids}  

        # Loop over model_ids to add bikes within the budget
        for m_id in model_ids:
            model_cost = self.bicycle_models['cost'].iloc[m_id - 1]

            # Calculate the max allowed count for bike based on proportion of budget
            max_count_for_bike = max(1, budget // (4 * model_cost)) 

            # While loop to add bikes within the budget
            while total_cost <= budget:
                if (model_cost + total_cost) <= budget and bike_count[m_id] < max_count_for_bike:
                    bikes_selected.append(m_id)
                    total_cost += model_cost
                    bike_count[m_id] += 1  
                else:
                    break

        count_bikes = collections.Counter(bikes_selected)
        model_ids = [x-1 for x in count_bikes.keys()]
        model_df = self.bicycle_models[['brand', 'type', 'size', 'cost', 'instore']].iloc[model_ids]
        model_df.insert(0, 'frequency', count_bikes.values())
        
        return model_df
    
    #####################################################################
        ## test
    ####################################################################
    def test_select_success(self, budget):
        '''Test select works'''

        confirm_message, selected_df, images = select_instance.select(allocation=100, 
                                                              budget=budget)
        
        assert isinstance(confirm_message, widgets.HTML)
        assert isinstance(selected_df, pd.DataFrame)
        assert isinstance(images, pd.Series)
        assert not selected_df.empty, 'Expected bikes to have been selected'

        total_cost = selected_df['cost'].sum()
        assert total_cost <= budget, f"Total cost {total_cost} exceeds budget"

        return True

############################################################################
    #### MAIN
###########################################################################
    
if __name__ == '__main__':
    database = Database('database-TEST15.db')
    select_instance = BikeSelect(database)

    if select_instance.test_select_success(budget=20000):
        print('Test select passed')