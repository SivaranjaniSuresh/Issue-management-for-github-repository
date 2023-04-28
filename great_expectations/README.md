# Data Quality Check with Great Expectations

As part of our project, we have conducted a comprehensive data quality check on the records obtained from the Github API and stored in Snowflake. The purpose of this data quality check was to ensure that we deliver accurate and reliable data to our clients, and to guarantee data availability with the utmost precision.

## Quality Checks
We have developed tests at both the table and column levels. At the table level, we checked that the record count fell within the specified minimum and maximum values. At the column level, we focused on key attributes, including CREATE_BY, ID, ISSUE_NUMBER, ISSUE_URL, REPO_NAME, REPO_OWNER, STATE, TITLE, and UPDATED_AT.

Our quality checks revolve around the mandatory fields outlined in the Github policy. We have ensured that these fields cannot be null and have also incorporated checks for unique issue numbers and issue URLs for each issue created.

## Great Expectations
To streamline the data validation process and ensure consistent quality checks, we have automated the process of retrieving data from Snowflake and passing it to Great Expectations for validation. The validation results are then hosted on an AWS S3 bucket using its static web hosting feature.

We have created an expectations file named `github_issues_suite.json` that contains the following expectations:

```json
{
  "data_asset_type": null,
  "expectation_suite_name": "github_issues_suite",
  "expectations": [
    {
      "expectation_type": "expect_table_row_count_to_be_between",
      "kwargs": {
        "max_value": 10000,
        "min_value": 1
      }
    },
    {
      "expectation_type": "expect_table_columns_to_match_set",
      "kwargs": {
        "column_set": [
          "TITLE",
          "CREATED_BY",
          "ISSUE_URL",
          "ID",
          "BODY",
          "STATE",
          "UPDATED_AT",
          "REPO_NAME",
          "ISSUE_NUMBER",
          "REPO_OWNER"
        ]
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_unique",
      "kwargs": {
        "column": "ID"
      }
    },
    {
      "expectation_type": "expect_column_values_to_be_unique",
      "kwargs": {
        "column": "ISSUE_URL"
      }
    },
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {
        "column": "ID"
      }
    },
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {
        "column": "ISSUE_URL"
      }
    }
  ]
}

