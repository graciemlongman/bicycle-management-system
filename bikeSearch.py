# searching functions
from database import *
import pandas as pd
import ipywidgets as widgets


class BikeSearch():
    '''
    A class handling search functions which allow the store manager
    to search for bicycles by brand, type or frame size.
    Results display rental status (picture eventually) and price

    FUNCTIONS:
    - search (database, term, parameter) -> dataframe
        Returns dataframe matching the search term
    
    HELPER FUNCTIONS:
    - _read_db (sqlite3 database) -> dataframe
        Reads in the database from sqlite to a pandas dataframe

    - _get_display_cols (str) -> list
        returns a list of appropriate columns to be displayed to user
    '''
    def __init__(self):
        '''
        Begin the search process
        '''

    def search(self, database, term, parameter):
        '''
        Search function
        Args:
        --------
        database ()
        term (str): should be brand, type or (frame) size
        parameter (str): the brand, type or size manager wishes to search by
        '''
        bicycles_df = self._read_db(database)

        #filter based on users inputed search params
        searched_df = bicycles_df[bicycles_df[term] == parameter]

        #choose display cols according to search term
        display = self._get_display_cols(term)

        #display relevant info
        display_df = searched_df[display]

        if len(display_df) > 0:
            return display_df
        else:
            return widgets.HTML(value=f"<span style='color: red;'>No items match your search for {term} = {parameter}</span>")
        
    ##################################################################
            ## helper methods
    #################################################################
    
    def _read_db(self, database):
        '''
        Use pandas to read in the database
        '''
        try:
            conn = database.connection
            bicycles_df = pd.read_sql('''SELECT * FROM bicycle_models bm 
                                      INNER JOIN bicycle_inventory bi 
                                      ON bm.model_id = bi.model_id''', con=conn, 
                                      index_col = ['id'])
            return bicycles_df
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
    def _get_display_cols(self, term):
        '''
        Simple function which selects the correct display cols based on search
        '''
        if term == 'brand':
            return ['status', 'type', 'size', 'daily_rental_rate', 'weekly_rental_rate']

        elif term == 'type':
            return ['status', 'brand', 'size', 'daily_rental_rate', 'weekly_rental_rate']
        
        elif term == 'size':
            return ['status', 'brand','type', 'daily_rental_rate', 'weekly_rental_rate']
        
    ##############################################################
        ## tests
    #############################################################
    
    def test_search_valid_input(self, database):
        '''Test search returns correct dataframe for a valid term and parameter'''
        term = 'type'
        parameter = 'mountain bike'
        result = self.search(database, term, parameter)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        
        return True

###################################################################

if __name__ == '__main__':
    database = Database('database.db')
    search_instance = BikeSearch()

    if BikeSearch.test_search_valid_input(search_instance, database):
        print('Test search valid input passed')