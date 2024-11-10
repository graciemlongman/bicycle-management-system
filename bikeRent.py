#rental functions
from database import *
import membershipManager as m

import pandas as pd
from datetime import datetime, timedelta
import ipywidgets as widgets

class BikeRent():
    ''' 
    A class containing functions that allow the store manager to 
    rent out bicycles

    FUNCTIONS:
    - rent(self, database, member_id, bicycle_id, rent_date_, rent_duration)
        This function is called to complete the rent process
    
    HELPER FUNCTIONS:
    - _perform_checks(self, database) -> bool
        Checks if the bike is available and if the membership is active, and
        that the rental limit is not exceeded

    - _update_db(self,database, rent_date, rental_days) -> bool

    - _confirmation_message(self, database, rate) -> dataframe
    '''

    def __init__(self):
        '''
        Begin the renting process
        '''
    
    def rent(self, database, member_id, bicycle_id, rent_date_, rent_duration):
        '''
        Overall main function: perform checks then update the database
        Args:
        -----------
        databse (obj inst):
        member_id (int):
        bicycle_id (int):

        Returns:
        -----------
        Data frame showing line added to database and printed confirmation
        message
        '''
        #get id values
        self.m_id = member_id
        self.b_id = bicycle_id

        #get dates
        self.rent_date = rent_date_
        if self.rent_date is None:
         return widgets.HTML(value="<span style='color: red;'>Please enter a valid date</span>")
        
        self.rental_days = int(rent_duration)
        if self.rental_days == 0:
            return widgets.HTML(value="<span style='color: red;'>You must rent your bike for at least one day</span>")

        if self._perform_checks(database):
            if self._update_db(database):
                return self._confirmation_message(database)
        else:
            return widgets.HTML(value="<span style='color: red;'>You have reached your rental limit or entered incorrect ID</span>")

    ##########################################################
        ## Helper methods
    ############################################################

    def _perform_checks(self, database):
        '''
        Performs necessary checks based on information provided
        by the store manager
        Check bike ID is valid and bike is available
        Args:
        ----------------

        '''
        bicycle_check =  database.check(col='id', col2='status', 
                          table='bicycle_inventory', 
                          check=self.b_id, check2 = 'available')
        
        #if bike is available, check member
        if bicycle_check:
            memberships = m.load_memberships()

            if m.check_membership(self.m_id, memberships):

                limit = m.get_rental_limit(self.m_id, memberships)

                num_rented = database.query(f'''SELECT COUNT (b.status)
                FROM bicycle_inventory b INNER JOIN rental_hist r ON b.id=r.id
                WHERE b.status='Rented' AND r.member_id={self.m_id}''')
                
                if num_rented[0][0] < limit:
                    return True
                else:
                    return False

        return bicycle_check   
    
    def _update_db(self,database):
        '''
        Updates necessary information in the database
        Bicycle rent status -> rented
        Record transaction in rental history
        '''
        return_date = (self.rent_date + timedelta(days=self.rental_days))

        #edit bike table
        updated = database.alter_row(table='bicycle_inventory', 
                           col = 'status', new_col_value='rented', 
                           key='id', key_value=self.b_id)

        #insert into rental history
        inserted = database.add_row(table='rental_hist (id, rental_date, return_date, member_id)', 
                                    values=(self.b_id, self.rent_date, 
                                            return_date, self.m_id))

        return updated and inserted
    
    def _confirmation_message(self, database):
        '''
        Selects necessary data and displays confirmation message
        '''
        model_id = database.query(f'SELECT model_id FROM bicycle_inventory WHERE id = {self.b_id}')[0][0]
        weekly_rate = database.query(f'SELECT weekly_rental_rate FROM bicycle_models WHERE model_id = {model_id}')[0][0]
        
        if self.rental_days >7 and len(weekly_rate)>0:
            rate = 'daily_rental_rate, bm.weekly_rental_rate' 
        else:
            rate = 'daily_rental_rate'
        
        query = (f''' SELECT bi.id, bm.brand, bm.type, bm.{rate}, r.return_date
                    FROM bicycle_inventory bi 
                    INNER JOIN rental_hist r ON bi.id = r.id
                    INNER JOIN bicycle_models bm ON bi.model_id = bm.model_id
                    WHERE r.log = ((SELECT MAX(log) FROM rental_hist))
                        ''')
        conn = database.connection
        details = pd.read_sql(query, conn, index_col = ['id'])

        if details is not None:
            return details
        
    #####################################################################
        ## test
    ####################################################################
    
    def test_rent_success(self):
        '''Test that rent successfully processes a valid rental'''
        member_id = 1040
        bicycle_id = 54
        rent_date = datetime.strptime('2024/10/16','%Y/%m/%d').date()
        rent_duration = 10

        # Run the rent method
        result = rent_instance.rent(database, member_id, bicycle_id, rent_date, rent_duration)

        # Check that the result includes a DataFrame and a confirmation message widget
        assert isinstance(result, pd.DataFrame), "Expected result to be a DataFrame"
        assert not result.empty, "Expected rental details DataFrame to be non-empty"

        #check database was altered
        status = database.query(f'SELECT status FROM bicycle_inventory WHERE id={bicycle_id}')[0][0]
        assert status == 'rented', f"Expected status to be 'rented', but got {status}"

        #revert changes
        database.alter_row(table='bicycle_inventory', col = 'status',
                            new_col_value='available', key='id', 
                            key_value=bicycle_id)
        database.delete_row(table='rental_hist', key = 'log', 
                        key_value = '(SELECT MAX(log) FROM rental_hist)')
        return True

############################################################################
    #### MAIN
###########################################################################
    
if __name__ == '__main__':
    database = Database('database.db')
    rent_instance = BikeRent()

    if rent_instance.test_rent_success():
        print('Test rent success passed')

