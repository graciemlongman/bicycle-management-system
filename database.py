# Database Operations
import sqlite3
from datetime import datetime, date
import random
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pickle

class Database:
    '''
    Class to manage database operations for a given database.
    Includes creating the database, creating tables and data cleaning
    Operations including altering rows, adding rows and checking information

    FUNCTIONS:
    - __init__(self, db_name)
        Establish connection to the database

    - create_table(self, table_name)
        Create table designed specifically to load in text data. 
        Normalised to 1NF by keeping atomic values only

    - clean_load_files_to_table(self, table_name, file_path)
        Read in text file line by line, clean each line and insert to database

    - normalise_database(self)
        This function adjusts the structure of the database to 3NF. See ReadMe.
            - 'rental_hist'
            - 'bicycle_models'
            - 'bicycle_inventory'
            - 'images'
    
    - load_data()
        Ties together all steps when initialising database: create_table, 
        clean_load_files_to_table, normalise_database. Also adds 5 bikes to 
        bicycle_models table, used for recommendations to expanding inventory.

    - read_line(self, col, table, id, member_id = None) -> list of tuples
        Given bicycle id read line from database

    - query(self, query) -> list of tuples
        General query function. Allows the user to input their query manually 
        without needing to use the cursor etc

    - check(self, table, col, check, col2= None, check2 = None) -> bool
        Used in bicycleRent and bicycleReturn to check status and id etc
        Returns bool if status/id is as needed, eg status must be 'rented' to 
        return a bike

    - add_row(self, table, values) -> bool
        Insert row into table. Returns true if complete

    - alter_row(self, table, col, new_col_value, key, key_value) -> bool
        Alter row in table. Returns true if complete
    
    - delete_row(table, key, key_value) -> bool
        Delete row in table. Return true if complete
    
    - clear_db(self)
        Clear entire database and close sqlite connection.
    

    HELPER FUNCTIONS:

    - _clean(self, table_name, line) -> list

    - _parse_weekly_rate(self, line) -> list 
        Insert NULL value to weekly_rate column if necessary

    - _parse_date(self, x) -> date
        Parse dates to the correct formats
    
    - _get_dict_of_pickled_photos() -> dict
        returns dict of {brand:img} of photos


    '''

    def __init__(self, db_name):
        '''
        Establish connection to SQLite database
        This also creates the database file the first time its called.
        Args:
        -------------
        db_name (str): Name of the database. Should have the .db suffix.
        '''
        self.db_name = db_name
        self.table_names = []

        try:
            self.connection = sqlite3.connect(self.db_name, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            
            self.cursor = self.connection.cursor()
            print(f'Connected to {self.db_name}')
        except sqlite3.Error as e:
            print(f'Error connecting to database: {e}')

    def create_table(self, table_name):
        '''Create table
           Args:
           ---------
           table_name (str): determines which SQL statement is used
        '''
        self.table_names.append(table_name)
        create_statements = {
            'rental_hist' : '''CREATE TABLE IF NOT EXISTS rental_hist (
                        id INTEGER,
                        rental_date DATE,
                        return_date DATE,
                        member_id INTEGER
                        );''',

            'bicycles' : '''CREATE TABLE IF NOT EXISTS bicycles (
                        id INTEGER,
                        brand VARCHAR(20),
                        type VARCHAR(20),
                        size VARCHAR(20),
                        daily_rental_rate VARCHAR(20),
                        weekly_rental_rate VARCHAR(20),
                        purchase_date DATE,
                        condition VARCHAR(20),
                        status VARCHAR(20)
                        );''' }
        
        #get the correct sql statement according to table name
        #or use create table query provided
        create = create_statements.get(table_name)
        if create is None:
            print(f'Unknown table name: {table_name}')
            return
        
        try:
            self.cursor.execute(create)
            self.connection.commit()
            print(f'Table: {table_name} created successfully \n')
        except sqlite3.Error as e:
            print(f'Error creating table: {e}')
    
    def clean_load_files_to_table(self, table_name, file_path):
        '''
        Clean data and Load files into sqlite table
        Args:
        -------
        table_name (str): store table name you are cleaning
        file path (str): Load in and read specified .txt file
        '''
        try:
            #open file
            with open(file_path, 'r') as f:
                #skip header line
                next(f)
                
                #loop through file and clean then insert each row into the table
                for l in f:
                    clean_data = self._clean(table_name, l)
                    if clean_data is not None:
                        value_holder = '(' + ('?,' * (len(clean_data)-1))  + '?)'
                        self.cursor.execute(f'INSERT INTO {table_name} VALUES {value_holder}', clean_data)
                    else:
                        pass

                self.connection.commit()
            print(f'{file_path} loaded into {table_name} successfully\n')

        except sqlite3.Error as e:
            print(f'Error loading files to table: {e}')
        except FileNotFoundError:
            print(f'File not found {file_path}')
    
    def normalise_database(self):
        '''Normalise the database.

            Create bicycle_inventory table with attributes specfific to model of bike 
            Copy across attributes from bicycles table, assign model_id and cost
            Assign each bike in the inventory its model_id
            
            Create table bicycle_inventory, containing every bike in shop rather than each unique model
        
            Drop old table bicycles

            Add primary key to rental history

            Create table images - stores an image per brand of bike
        '''
        self.table_names.append('bicycle_models')
        self.table_names.append('bicycle_inventory')
        self.table_names.append('images')
        
        #get data to populate bicycle_models
        bicycle_costs = random.sample(range(500,3000), 33)
        unique_models = self.cursor.execute('SELECT DISTINCT brand, type, size, daily_rental_rate, weekly_rental_rate FROM bicycles;').fetchall()
        self.connection.commit()

        #create table models
        try:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS bicycle_models (
                    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand VARCHAR(20),
                    type VARCHAR(20),
                    size VARCHAR(20),
                    daily_rental_rate VARCHAR(20),
                    weekly_rental_rate VARCHAR(20),
                    cost INTEGER,
                    instore VARCHAR(20)); ''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Error creating models table {e}')

        #populate models table
        try:
            for cost, (brand, type, size, daily_r, weekly_r) in zip(bicycle_costs, unique_models):
                self.cursor.execute('''INSERT INTO bicycle_models (brand, type, size, daily_rental_rate, weekly_rental_rate, cost, instore)
                        VALUES (?,?,?,?,?,?,?)''', (brand, type, size, daily_r, weekly_r, cost, 'yes'))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Error populating table {e}')

        #-------------------------------------
        #create inventory table
        try:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS bicycle_inventory (
                    id INTEGER PRIMARY KEY,
                    model_id INTEGER,
                    purchase_date DATE,
                    condition VARCHAR(20),
                    status VARCHAR(20));''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Error creating table \'bicycle_inventory\' {e}')

        # copy over data which can be copied into table
        try:
            self.cursor.execute('''INSERT INTO bicycle_inventory (id, purchase_date, condition, status)
                SELECT id, purchase_date, condition, status
                FROM bicycles;''')
        except sqlite3.Error as e:
            print(f'Error copying data into table \'bicycle_inventory\' {e}')
        
        #now match the model id from above to each bike in the inventory
        match_model_id = []
        bicycles = self.query('SELECT brand, type, size FROM bicycles')

        for bike in bicycles:
            model_id = self.query(f"SELECT model_id FROM bicycle_models WHERE brand='{bike[0]}' AND type='{bike[1]}' AND size='{bike[2]}'")
            match_model_id.append(model_id)

        for idx , model_id in enumerate(match_model_id):
            self.cursor.execute(f'''UPDATE bicycle_inventory SET model_id=?
                    WHERE id=?;''', (model_id[0][0], idx+1))
        
        #no longer have need for bicycle table
        self.cursor.execute('''DROP TABLE IF EXISTS bicycles''')
        self.connection.commit()     

        #---------------------
        try:
            #add primary key to rental history table
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS new_rental_hist (
                                        log INTEGER PRIMARY KEY AUTOINCREMENT,
                                        id INTEGER,
                                        rental_date DATE,
                                        return_date DATE,
                                        member_id INTEGER);''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Error creating table: {e}')

        try:
            #copy data over into new_rental_hist
            self.cursor.execute('''INSERT INTO new_rental_hist (id, rental_date, return_date, member_id)
                                SELECT id, rental_date, return_date, member_id FROM rental_hist;''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Error copying data over: {e}')
        
        #drop table and rename
        try:
            self.cursor.execute('''DROP TABLE IF EXISTS rental_hist''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Error dropping table: {e}')

        self.cursor.execute('''ALTER TABLE new_rental_hist RENAME TO rental_hist''')
        self.connection.commit()

        #------------------
        try:
            #create image table
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS images (
                                    brand VARCHAR(20) PRIMARY KEY,
                                    photo BLOB);''')
            self.connection.commit()
        except sqlite3.Error as e:
            print(f'Failed to create images table')
        
        photo_dict = self._get_dict_of_pickled_photos()
        
        #populate images table
        for brand, photo in photo_dict.items():
            try:
                self.cursor.execute('''INSERT INTO images (brand, photo)
                                    VALUES (?,?)''', (brand, photo))
                self.connection.commit()
            except sqlite3.Error as e:
                print(f'Failed to add data to images: {e}')

        print('Database normalised successfully\n')

    def load_data(self):
        '''
        Ties together all steps involving initialising the database.
        - Create tables to store text files
        - Clean and read in data from text files
        - Normalise database
        '''
        tables={'rental_hist': 'data\Rental_History.txt', 'bicycles': 'data\Bicycle_info.txt'}
        for name, path in tables.items():
            self.create_table(name)
            self.clean_load_files_to_table(name, path)

        self.normalise_database()

        # add bikes used to expand inventory in select module
        table = 'bicycle_models (brand, type, size, daily_rental_rate, weekly_rental_rate, cost, instore)'

        self.add_row(table=table, values=('trek','electric bike','medium','33/day','NULL',2500,'no'))
        self.add_row(table=table, values=('giant','electric bike','medium','30/day','NULL',1500,'no'))
        self.add_row(table=table, values=('cannondale','electric bike','medium','34/day','NULL',2600,'no'))
        self.add_row(table=table, values=('specialized','road bike','medium','35/day','NULL',3500,'no'))
        self.add_row(table=table, values=('bianchi','electric bike','medium','30/day','NULL',1000,'no'))

    
    #############################################################
        ##  OPERATIONS

    def read_line(self, col, table, id, member_id = None):
        '''
        Read line from database conditional on bicycle id
        Args:
        ---------
        bicycle_id (int):
        member_id (int):
        '''
        try:
            query = f'SELECT {col} FROM {table} WHERE id=?'
            parameters = (id,)

            if member_id:
                query += f' AND member_id=?'
                parameters += (member_id,)
            
            self.cursor.execute(query, parameters)
            return self.cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f'Error reading {col} from table {table}: {e}')

    def query(self, query):
        '''
        An open-ended general query function. User must supply their own query
        Args:
        --------
        query (str): SQL query statement to be executed
        '''
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f'Error executing query {query}: {e}')
    
    def check(self, table, col, check, col2= None, check2 = None):
        '''
        Validates inputs against the database.
        Can optionally check two columns
        Args:
        ------------
        table (str): appropriate table to perform check for
        col (str): The column you want to check, eg., bicycle id
        check (str): The value you are checking for, eg., 10 
        col2 (str): as above
        check2 (str): as above
        '''
        try:
            query = f'SELECT {col} FROM {table} WHERE {col}=?'
            parameters = (check,)

            if col2 and check2:
                query += f' AND {col2}=?'
                parameters += (check2,)

            self.cursor.execute(query, parameters)
            
            #returns true or false
            return len(self.cursor.fetchall())>0
            
        except sqlite3.Error as e:
            print(f'Error checking details from database: {e}')
            return False
        
    def add_row(self, table, values):
        ''''
        Insert row into table
        Args:
        ------
        table (str): The table you wish to add a row too
        values (tuple or list): The values for each col in that table
        '''
        try:
            value_holder = '(' + ('?,' * (len(values)-1))  + '?)'
            query = f'INSERT INTO {table} VALUES {value_holder}'
            parameters = values

            self.cursor.execute(query, parameters)
            self.connection.commit()

            print(f'Data inserted to table \'{table}\' successfully')
            return True
        except sqlite3.Error as e:
            print(f'Error inserting into table \'{table}\': {e}')
            return False
    
    def alter_row(self, table, col, new_col_value, key, key_value):
        '''
        Alter existing information in the database
        Args:
        -------
        table (str): The table you wish to alter
        col (str): The column you wish to alter
        new_col_value (): New value for col
        key (str): conditional
        key_value (str): conditional value
        '''
        try:
            self.cursor.execute(f'''UPDATE {table} 
                                    SET {col}=?
                                    WHERE {key}=?''',
                                    (new_col_value, key_value))
            self.connection.commit()

            print(f'Successfully altered table \'{table}\'.')
            return True
        
        except sqlite3.Error as e:
            print(f'Error altering database: {e}')
            return False

    def delete_row(self, table, key, key_value):
        '''delete line from database'''
        try:
            self.cursor.execute(f'''DELETE FROM {table}
                                    WHERE {key}={key_value}''')
            self.connection.commit()
            
            print(f'Successfully deleted row from table \'{table}\'.')
            return True
        
        except sqlite3.Error as e:
            print(f'Error deleting row: {e}')
            return False

    #############################################################
            ## Clear database
    
    def clear_db(self):
        '''
        Clears entire databse
        '''
        print('This action clears your entire database. Are you sure? y/n')
        bool = str(input())

        if bool == 'y':
            try:
                #drop tables, using the list of tables stored in your class
                for name in self.table_names:
                    self.cursor.execute(f'DROP TABLE IF EXISTS {name}')
                    self.connection.commit()
                self.connection.close()
                print('Database cleared successfully')

            except sqlite3.Error as e:
                print(f'Error clearing database: {e}')

    ##################################################################
            ## helper methods
    #################################################################

    def _clean(self, table_name, line):
        '''
        Clean each row inputted from the given database.
        Parse dates, handle invalid dates, missing data
        Args:
        -------
        table_name: toggles for specific actions which only affect one data set
        line: line from text file that python interpreter has read 
        '''
        #get a list of inputs
        #convert ; into comma (separate weekly/daily rates)
        inputs_list = line.strip().replace(';',',').split(',')
        inputs_list = [x.lower() for x in inputs_list]
        
        #add null value for bikes with no weekly rate
        if table_name == 'bicycles':
            inputs_list = self._extract_weekly_rate(inputs_list)
            inputs_list = self._replace_missing_brand(inputs_list)
            inputs_list[4] = inputs_list[4].replace('£', '/day')
        else:
            inputs_list[1] = inputs_list[1].replace('-', '/')
            inputs_list[2] = inputs_list[2].replace('-', '/')
        
        inputs_list = self._parse_dates(inputs_list, table_name)

        return inputs_list

    def _extract_weekly_rate(self, inputs_list):
        '''
        Adds a NULL value after the daily rate if no weekly rate is present
        Args:
        --------
        line (list): to check length of list
        '''
        if len(inputs_list) == 8:
            inputs_list.insert(5, 'NULL')
        return inputs_list

    def _replace_missing_brand(self, inputs_list):
        '''
        Impute missing brand values. The brand directly relates to price.
        Args:
        -----------
        inputs_list (list)
        '''
        match_brand_by_price = { '26' : 'giant',
                                '27' : 'cannondale',
                                '28' : 'trek',
                                '29' : 'specialized',
                                '30' : 'bianchi'}
        
        if inputs_list[1] == 'missing':
            inputs_list[1] = match_brand_by_price.get(inputs_list[4][0:2])

        return inputs_list 

    def _parse_dates(self, inputs_list, table_name):
        '''
        Validate dates from a row of input data
        A date is invalid if
            it is after today
        Args:
        -----------
        x (str): each item of the list as looped through in `_clean`
        '''
        if table_name == 'bicycles':
            x = inputs_list[6]
            try:
                #convert dates to date objects
                x = datetime.strptime(x, '%d/%m/%Y').date()
    
                inputs_list[6] = x if x <= date.today() else None
            
            #if invalid date format - reassign date to start of business
            except ValueError:
                inputs_list[6] = datetime.strptime('2021/01/01','%Y/%m/%d').date()

        if table_name == 'rental_hist':
            x = inputs_list[1]
            y = inputs_list[2]
            try:
                #convert dates to date objects
                rent_date = datetime.strptime(x, '%Y/%m/%d').date()
                return_date = datetime.strptime(y, '%Y/%m/%d').date()

                #check return date is not before rent date
                #if they are, swap them
                if return_date < rent_date:
                    rent_date, return_date = return_date, rent_date
                
                inputs_list[1] = rent_date if rent_date <= date.today() else None
                inputs_list[2] = return_date if return_date <= date.today() else None
                
            #if invalid date format
            except ValueError as e:
                return None
        
        return inputs_list
  
    def _get_dict_of_pickled_photos(self):
        '''
        Reads in and pickles images to then be inserted to df
        Returns:
        -----------
        dict of {brand:image} of photos
        '''
        brands = ['bianchi', 'cannondale', 'giant', 'specialized', 'trek']
        images = {}
        
        for brand in brands:
            try:
                img = mpimg.imread(f'bike_images/{brand}-bike.jpg')
                images[brand] = pickle.dumps(img)
            except FileNotFoundError:
                print(f"Image for {brand} not found.")
                images[brand] = None 

        return images

    ######################################################################
            ## tests
    #####################################################################
    def test_data_not_none(self):
        '''test data not none'''
        if database is not None:
            return True
        else:
            print('Error:')
    
    def test_data_not_empty(self):
        '''Test each normalized table is not empty'''

        # Query each table and fetch all rows
        self.inventory = self.query('SELECT * FROM bicycle_inventory')
        self.models = self.query('SELECT * FROM bicycle_models')
        self.history = self.query('SELECT * FROM rental_hist')
        self.images = self.query('SELECT * FROM images')

        # Check if each table has data
        if not self.inventory:
            print("Error: No data in table 'bicycle_inventory'")
            return False
        if not self.models:
            print("Error: No data in table 'bicycle_models'")
            return False
        if not self.history:
            print("Error: No data in table 'rental_hist'")
            return False
        if not self.images:
            print('Error: no data in table images')
            return False
        # All tables are non-empty
        return True

    def test_data_columns(self):
        '''Test each table has the correct columns as expected'''

        expected_columns = { 
        'rental_hist' : ['log', 'id', 'rental_date', 'return_date', 'member_id'],
        'bicycle_inventory' : ['id', 'model_id', 'purchase_date', 'condition', 'status'],
        'bicycle_models' : ['model_id', 'brand', 'type', 'size', 'daily_rental_rate', 'weekly_rental_rate', 'cost', 'instore'],
        'images' : ['brand', 'photo']}

        for table, expected_names in expected_columns.items():
            info = self.query(f'PRAGMA table_info({table})')
            col_names = [item[1] for item in info]

            message = f'in {table}, expected {expected_names}, got {col_names}'
            assert col_names == expected_names, message

        return True
    

###########################################################################
###########################################################################
    #### MAIN
###########################################################################
###########################################################################
    
if __name__ == '__main__':
    database = Database('database.db')

    #The function below can only be ran once. It cleans the data and loads it 
    #in to the database, then normlaises the data.
    #database.load_data()

    if database.test_data_not_none():
        if database.test_data_not_empty():
            if database.test_data_columns():
                print('database initialised- all tests passed')
