#rental functions
from database import *

from datetime import date, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import collections
import numpy as np
import ipywidgets as widgets

import membershipManager as m

##############################
#          TO DO             #
##############################
# display message if budget too low
# could return any leftover budget ?
# return total cost?
# display both dataframes? 
# visualisations?
#testing
#docstrings

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
        Dataframe of bikes that should be selected for purchase
        '''
        self.budget = budget

        #calculate overall score for each bicycle in inventory
        id_and_scores = self._assign_score()
  
        #sorted by score with highest first, older, damaged bikes more likely to be replaced
        top10_models = self._sort_by_score_and_get_model_id(id_and_scores)

        #inventory will be maintained for up to 70% of budget allocation
        maintain_budget = (allocation/100) * self.budget
        maintain_df = self._select_bikes(budget=maintain_budget, model_ids = top10_models)


        #after budget has been allocated, rest goes to new bikes
        new_bike_budget = self.budget - maintain_budget
        new_models = self.bicycle_models[self.bicycle_models['instore'] == 'no']

        new_df = self._select_bikes(budget=new_bike_budget, model_ids = [x-1 for x in new_models.index])
        
        # confirmation = widgets.HTML(value=f'Overall budget was £{self.budget}, with {allocation}% of the budget allocated to maintaining the current inventory')

        return widgets.HTML(value=f'Overall budget was £{self.budget}, with {allocation}% of the budget allocated to maintaining the current inventory'), pd.concat([maintain_df, new_df])

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

        ax.set_title('Rental frequency of bikes, by member and model', fontsize=20)
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
        [[bike_id, score],
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
        Returns dataframe of selected bikes within budget
        '''
        cost=0 
        bikes_selected=[]
      
        for m_id in model_ids:
            cost += self.bicycle_models['cost'].iloc[m_id]
            if cost <= budget:
                bikes_selected.append(m_id)

        count = collections.Counter(bikes_selected)
        bike_ids = [x-1 for x in count.keys()]
        model_df = self.bicycle_models[['brand', 'type', 'size', 'cost', 'instore']].iloc[bike_ids]
        model_df.insert(0, 'frequency', count.values())
        
        return model_df


############################################################################
    #### MAIN
###########################################################################
    
if __name__ == '__main__':
    database = Database('database9.db')

    #BikeSelect(database).select(database, allocation=70, budget=20000)
    BikeSelect(database).visualise()