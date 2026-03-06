import sys
import os
import pandas as pd
from pandas import DataFrame
from dataclasses import dataclass
import numpy as np
import glob

from src.utils.logger import logging
from src.utils.exception import Custom_exception
from sqlalchemy import create_engine
import pymysql


@dataclass
class DataCleaningConfig:
    is_airflow = os.getenv("IS_AIRFLOW", "false").lower() == "true"

    if is_airflow:
        input_path = None
        output_path = None
    else:
        input_path = "data"
        output_path = "artifacts/data_cleaned.csv"

    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_db = os.getenv("MYSQL_DB", "ecommerce_recommender_system")
    mysql_conn = (
        f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
    )
    tables = ["shirts", "women_clothes", "watches"]
    cleaned_table = "data_cleaned"


class DataCleaner:
    """
    Remove nan values from the data
    """

    def __init__(self):
        self.data_cleaner_config = DataCleaningConfig()
        self.engine = create_engine(self.data_cleaner_config.mysql_conn)

    def load_data(self):
        try:
            logging.info("Loading data from MySQL database")
            dfs = []
            for table in self.data_cleaner_config.tables:
                df = pd.read_sql_table(table, self.engine)
                dfs.append(df)

            df = pd.concat(dfs, ignore_index=True)
            logging.info("Data loaded successfully")
            return df
        except Exception as e:
            logging.info(f"Error in loading data: {str(e)}")
            raise Custom_exception(e, sys)

    def check_for_na(self, df: DataFrame):
        try:
            logging.info("Checking for 'na' values")
            df_na = df[
                df.applymap(lambda x: str(x).strip().lower() == "na").any(axis=1)
            ]
            print(f"Total number of records that has 'na': {len(df_na)}")

            columns_na = df.applymap(lambda x: str(x).strip().lower() == "na").sum()
            print(f"\ncolumn wise presence of 'na' \n{columns_na}")

        except Exception as e:
            logging.info(f"Error in checking NA values: {str(e)}")
            raise Custom_exception(e, sys)

    def find_mode(self, df: DataFrame):
        try:
            df_without_na = df[
                ~df.applymap(lambda x: str(x).strip().lower() == "na").any(axis=1)
            ]

            cols = df.select_dtypes(include=["object", "category"]).columns

            # Compute mode for each categorical column
            modes_dict = {}
            for col in cols:
                mode_values = df_without_na[col].mode()
                if not mode_values.empty:
                    modes_dict[col] = mode_values[
                        0
                    ]  # Take the first mode if multiple exist

            return cols, modes_dict
        except Exception as e:
            logging.info(f"Error in calculating replacement values: {str(e)}")
            raise Custom_exception(e, sys)

    def handling_na(self, columns, replacement_value, df: DataFrame, table_name):
        try:
            logging.info("Replacing 'na' values with mode")

            # Convert 'na' to pd.NA first
            df = df.replace("na", pd.NA)

            for col in columns:
                if col in df.columns:  # Fixed the condition here
                    df[col] = df[col].fillna(replacement_value[col])

            logging.info("Sucessfully replaced 'na' values")
            logging.info("Saving the cleaned data to MySQL")

            df.to_sql(table_name, self.engine, if_exists="replace", index=False)
            return df

        except Exception as e:
            logging.info(f"Error in handling NA values: {str(e)}")
            raise Custom_exception(e, sys)

    def clean_data(self):
        try:
            logging.info("Starting data cleaning process")
            df = self.load_data()
            self.check_for_na(df)
            cols, replace_value = self.find_mode(df)
            df_cleaned = self.handling_na(
                columns=cols,
                replacement_value=replace_value,
                df=df,
                table_name=self.data_cleaner_config.cleaned_table,
            )

            logging.info("Data cleaning process has been completed")
            return df_cleaned

        except Exception as e:
            logging.error(f"Error cleaning data: {str(e)}")
            raise Custom_exception(e, sys)
