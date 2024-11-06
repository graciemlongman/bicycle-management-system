#rental functions
from database import *

from datetime import datetime
import ipywidgets as widgets

##############################
#          TO DO             #
##############################
# error message

#testing
#docstrings

class BikeReturn():
    '''
    A class containing functions that allow the store manager to 
    return the rented bicycle by providing the bicycle's ID.

    FUNCTIONS:
    - return_bike(self, database, bicycle_id, actual_return_date, condition)
        This function is called to complete the return process
    
    HELPER FUNCTIONS:
    -  _check_id(database) -> bool

    - _inspect_and_update(database) -> bool

    - _calculate_charge(database) -> list

    - _confirmation_message(charge) ->
    '''

    def __init__(self):
        '''
        Begin the return process
        '''
    
    def return_bike(self, database, bicycle_id, actual_return_date, condition):
        '''
        Overall return process: validate inputs + update db
        '''
        self.b_id = bicycle_id
        self.condition = condition
        self.actual_return = actual_return_date
        
        if self._check_id(database):

            condition = self._inspect_and_update(database)

            charge = self._calculate_charge(database)

            return self._confirmation_message(charge)
        else:
            return widgets.HTML(value='Your bike is not ready to be returned.')

    
    ##############################################################
            ## Helper methods
    ##############################################################
            
    def _check_id(self, database):
        '''
        Performs necessary checks based on information provided
        by the store manager
        Check bike ID is valid and bike is currently rented
        Args:
        ----------------

        '''
        bicycle_check =  database.check(col='id', col2='status', 
                          table='bicycle_inventory', 
                          check=self.b_id, check2 = 'rented')
        
        return bicycle_check 
    
    def _inspect_and_update(self, database):
        '''
        Updates necessary information in the database.
        status -> Available unless bike is damaged
        Checks condition
        '''
        
        #adjust status if necessary
        status = 'available'
        if self.condition == 'damaged':
            status = 'under maintenance' 
        
        #update conition
        database.alter_row(table='bicycle_inventory', 
                        col = 'condition', new_col_value=self.condition, 
                        key='id', key_value=self.b_id)
        
        #update return date
        
        #update status
        database.alter_row(table='bicycle_inventory', 
                        col = 'status', new_col_value=status, 
                        key='id', key_value=self.b_id)

        return self.condition
    
    def _calculate_charge(self, database):
        '''
        Calculates a cost breakdown based on damage and late return
        Returns:
        ----------
        A list containing the cost breakdown and total cost
        '''
        #read in dates
        expected_return_date = database.read_line(col='return_date', 
                                                  table='rental_hist', 
                                                  id=self.b_id)[0][0]
        
        rent_date = database.read_line(col='rental_date', table='rental_hist', 
                                                    id=self.b_id)[0][0]
        
        actual_return_ = datetime.strptime(self.actual_return,'%Y/%m/%d').date()

        normal_daily_rate = int(database.query(f'''SELECT daily_rental_rate 
                                               FROM bicycle_models bm
                                               INNER JOIN bicycle_inventory bi ON bm.model_id = bi.model_id
                                               WHERE bi.id = {self.b_id} ''')[0][0][0:2])

        days_rented = (actual_return_ - rent_date).days
        days_overdue = max((actual_return_ - expected_return_date).days,0)

        #Charge calculation formulas:::::
        if days_rented % 7 == 0:
            weekly_rate = int(database.query(f'''SELECT weekly_rental_rate 
                                               FROM bicycle_models bm
                                               INNER JOIN bicycle_inventory bi ON bm.model_id = bi.model_id
                                               WHERE bi.id = {self.b_id} ''')[0][0][0:2])
            normal_fee = days_rented * weekly_rate
        else:
            normal_fee = days_rented * normal_daily_rate
        
        if days_overdue == 0:
            late_fee = 0
        else:
            late_fee = days_overdue * (normal_daily_rate + 5)
        
        if self.condition == 'damaged':
            damage_charge = 50
        else: 
            damage_charge = 0
        
        total_charge = normal_fee + late_fee + damage_charge

        return [normal_fee, late_fee, damage_charge, total_charge]
    
    def _confirmation_message(self, charge):
        '''
        Prints a confirmation message and cost breakdown of the bike
        Args:
        ----------
        condition (str): User inputs condition of bike
        charge (list): A list of the breakdown of charges as calculated in the
        _calculate_charge function
        '''
        success = widgets.HTML(value=f'''<h4>You have successfully returned your bike in {self.condition} condition!</h4>''')

        expected = widgets.HTML(value=f'Expected charge: £{charge[0]}')
        
        if charge[1] != 0:
            late = widgets.HTML(value=f'Late charge: £{charge[1]}')
        if charge[2] != 0:
            damage=widgets.HTML(value=f'Damage charge: £{charge[2]}')

        line = widgets.HTML(value='__________________________________')
        total = widgets.HTML(value=f'<h4>Total charge: £{charge[3]}</h4>')

        confirmation_box = widgets.VBox([success,expected,late,damage,line,total])

        return confirmation_box

    
###########################################################################
    #### MAIN
###########################################################################
    
if __name__ == '__main__':
    database = Database('database6.db')

    BikeReturn().return_bike(database, bicycle_id = 10, actual_return_date=2024/10/30, condition='Damaged')
    s = database.query('SELECT * FROM rental_hist')

    print(s)