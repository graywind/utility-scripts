# File Indexing Utility

The File Indexing Utility is a Python script (`fileindex.py`) that allows you to index and search file metadata in a MariaDB database. It recursively traverses a directory, collects file metadata, and stores it in the database for easy searching and analysis.

## Prerequisites

Before using the File Indexing Utility, make sure you have the following:

- Python 3.x installed
- MariaDB or MySQL server installed and running
- Database connection details (username, password, host, and database name)
- Python dependencies: `pymysql`, `python-magic`, and `python-dotenv`

## Setup

1. Clone or download the `fileindex.py` script to your local machine.

2. Install the required Python dependencies by running the following command in the terminal:

   ```bash
   pip install pymysql python-magic python-dotenv
   ```

3. Create a `.env` file in the same directory as `fileindex.py` and set the environment variables for your database connection details. Example:

   ```
   DB_USER=username
   DB_PASSWORD=password
   DB_HOST=localhost
   DB_NAME=file_index_db
   ```

4. Create the necessary database tables by running the script once. The tables `file_archive` and `file_metadata` will be created automatically.

## Usage

The File Indexing Utility supports the following commands:

- `index archive_name source_path`: Indexes the files in the specified `source_path` directory and associates them with the given `archive_name`.

- `search query`: Searches for files matching the specified `query` in the file metadata. Displays basic information about the matching files.

- `search-verbose query`: Searches for files matching the specified `query` in the file metadata. Displays detailed information about the matching files.

- `archive-summary`: Retrieves summary information about the indexed archives, including the number of files and the total size.

- `batch-summary`: Retrieves summary information about the indexed batches, including the archive name, batch ID, and total size.

- `purge-batch batch_id`: Deletes all file entries associated with the specified `batch_id`.

To use the utility, open a terminal or command prompt, navigate to the directory containing `fileindex.py`, and run the desired command using the following syntax:

```bash
python fileindex.py <command> <arguments>
```

Refer to the command descriptions above for the specific arguments required for each command.

## Example Usage

Here are a few examples to illustrate the usage of the File Indexing Utility:

- Index files in a directory:
  ```bash
  python fileindex.py index my_archive /path/to/source_directory
  ```

- Search for files by name:
  ```bash
  python fileindex.py search filename_query
  ```

- Search for files and display detailed information:
  ```bash
  python fileindex.py search-verbose filename_query
  ```

- Get summary information about indexed archives:
  ```bash
  python fileindex.py archive-summary
  ```

- Get summary information about indexed batches:
  ```bash
  python fileindex.py batch-summary
  ```

- Delete all files associated with a specific batch:
  ```bash
  python fileindex.py purge-batch batch_id
  ```

Remember to replace `archive_name`, `source_path`, `query`, and `batch_id` with the appropriate values for your use case.

## Note

The File Indexing Utility utilizes the `magic` library to determine file MIME types. Make sure you have the necessary file type detection libraries installed on your system for accurate results.

Please ensure that you have the necessary permissions and backup your data before performing any deletion operations using the utility.

For any further questions or issues, please

 refer to the script's source code or consult the documentation of the dependencies used.
