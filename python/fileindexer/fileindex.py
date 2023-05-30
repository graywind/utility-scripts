import os
import sys
import datetime
import uuid
import magic
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database connection variables from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Connect to MariaDB
conn = pymysql.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME
)

cursor = conn.cursor()

# Create the file_archive table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_archive (
        archive_id INT AUTO_INCREMENT PRIMARY KEY,
        archive_name VARCHAR(255) UNIQUE,
        uuid_name VARCHAR(36) UNIQUE
    )
""")

# Create the file_metadata table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS file_metadata (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(255),
        file_type VARCHAR(255),
        date_created DATETIME,
        date_modified DATETIME,
        posix_data VARCHAR(8),
        relative_path VARCHAR(255),
        file_size BIGINT,
        archive_id INT,
        batch_id VARCHAR(36),
        CONSTRAINT FK_ArchiveID FOREIGN KEY (archive_id) REFERENCES file_archive(archive_id),
        FULLTEXT(filename, file_type, relative_path)
    )
""")

# Function to recursively traverse the directory and collect file metadata
def index_files(archive_name, source_path, batch_id):
    # Check if archive_name already exists in file_archive table
    cursor.execute("SELECT archive_id FROM file_archive WHERE archive_name = %s", (archive_name,))
    archive_id = cursor.fetchone()

    if archive_id is None:
        # Archive does not exist, insert into file_archive table
        uuid_name = str(uuid.uuid4())
        cursor.execute("INSERT INTO file_archive (archive_name, uuid_name) VALUES (%s, %s)", (archive_name, uuid_name))
        archive_id = cursor.lastrowid
    else:
        archive_id = archive_id[0]

    for root, _, files in os.walk(source_path):
        for filename in files:
            file_path = os.path.join(root, filename)

            if os.path.isdir(file_path) or get_file_mime_type(file_path) == 'inode/x-empty':
                continue  # Skip directories and 'inode/x-empty' file types

            file_type = get_file_mime_type(file_path)
            stat_info = os.stat(file_path)
            date_created = datetime.datetime.fromtimestamp(stat_info.st_ctime).isoformat()
            date_modified = datetime.datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            posix_data = oct(stat_info.st_mode & 0o777)
            relative_path = os.path.relpath(file_path, source_path)
            file_size = stat_info.st_size
            metadata = (
                filename,
                file_type,
                date_created,
                date_modified,
                posix_data,
                relative_path,
                file_size,
                archive_id,
                batch_id
            )
            insert_file_metadata(metadata)


# Function to insert file metadata into MariaDB
def insert_file_metadata(metadata):
    insert_query = """
        INSERT INTO file_metadata
        (filename, file_type, date_created, date_modified, posix_data, relative_path, file_size, archive_id, batch_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, metadata)
    conn.commit()

# Function to retrieve the file MIME type using python-magic
def get_file_mime_type(file_path):
    return magic.from_file(file_path, mime=True)

# Function to convert bytes to the nearest whole unit (bytes, kilobytes, megabytes, or gigabytes)
def convert_bytes_to_nearest_unit(bytes_value):
    if bytes_value is None:
        return ""  # Return an empty string or handle it as desired

    units = ['bytes', 'KB', 'MB', 'GB']
    unit_index = 0
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024
        unit_index += 1
    return f"{bytes_value:.2f} {units[unit_index]}"

# Function to search for files in MariaDB
def search_files(query, verbose=False):
    search_query = """
        SELECT file_metadata.id, file_metadata.file_type, file_metadata.filename, file_metadata.relative_path, file_metadata.file_size,
               file_archive.archive_name, file_archive.uuid_name, file_metadata.batch_id
        FROM file_metadata
        INNER JOIN file_archive ON file_metadata.archive_id = file_archive.archive_id
        WHERE MATCH(file_metadata.filename, file_metadata.file_type, file_metadata.relative_path) AGAINST (%s IN BOOLEAN MODE)
    """
    cursor.execute(search_query, (query,))
    results = cursor.fetchall()
    for result in results:
        file_size = convert_bytes_to_nearest_unit(result[4])
        if verbose:
            print(f"ID: {result[0]}, MimeType: {result[1]}, Filename: {result[2]}, Path: {result[3]}, Size: {file_size}, Archive Name: {result[5]}, UUID Name: {result[6]}, Batch ID: {result[7]}")
        else:
            print(f"ID: {result[0]}, MimeType: {result[1]}, Filename: {result[2]}, Path: {result[3]}, Size: {file_size}, Archive Name: {result[5]}, UUID Name: {result[6]}")

# Function to delete entries with a specific batch_id
def purge_batch(batch_id):
    delete_query = "DELETE FROM file_metadata WHERE batch_id = %s"
    cursor.execute(delete_query, (batch_id,))
    deleted_rows = cursor.rowcount
    conn.commit()
    print(f"Deleted {deleted_rows} rows.")

# Function to get archive summary
def get_archive_summary():
    summary_query = """
        SELECT file_archive.archive_name, COUNT(file_metadata.id) AS file_count, SUM(file_metadata.file_size) AS total_size
        FROM file_archive
        LEFT JOIN file_metadata ON file_archive.archive_id = file_metadata.archive_id
        GROUP BY file_archive.archive_name
    """
    cursor.execute(summary_query)
    results = cursor.fetchall()
    for result in results:
        archive_name = result[0]
        file_count = result[1]
        total_size = convert_bytes_to_nearest_unit(result[2])
        print(f"Archive Name: {archive_name}, File Count: {file_count}, Total Size: {total_size}")

# Function to get batch summary
def get_batch_summary():
    summary_query = """
        SELECT file_archive.archive_name, file_metadata.batch_id, SUM(file_metadata.file_size) AS total_size
        FROM file_metadata
        INNER JOIN file_archive ON file_metadata.archive_id = file_archive.archive_id
        GROUP BY file_archive.archive_name, file_metadata.batch_id
    """
    cursor.execute(summary_query)
    results = cursor.fetchall()
    for result in results:
        archive_name = result[0]
        batch_id = result[1]
        total_size = convert_bytes_to_nearest_unit(result[2])
        print(f"Archive Name: {archive_name}, Batch ID: {batch_id}, Total Size: {total_size}")


# Main function
def main():
    if len(sys.argv) < 2:
        print("Invalid arguments. Usage:")
        print("fileindex.py index archive_name source_path")
        print("fileindex.py search query")
        print("fileindex.py search-verbose query")
        print("fileindex.py archive-summary")
        print("fileindex.py batch-summary")
        print("fileindex.py purge-batch batch_id")
        return

    command = sys.argv[1]
    if command == "index":
        if len(sys.argv) != 4:
            print("Invalid arguments for indexing. Usage: fileindex.py index archive_name source_path")
            return
        archive_name = sys.argv[2]
        source_path = sys.argv[3]
        batch_id = str(uuid.uuid4())
        index_files(archive_name, source_path, batch_id)

    elif command == "search":
        if len(sys.argv) != 3:
            print("Invalid arguments for search. Usage: fileindex.py search query")
            return
        query = sys.argv[2]
        search_files(query)

    elif command == "search-verbose":
        if len(sys.argv) != 3:
            print("Invalid arguments for search-verbose. Usage: fileindex.py search-verbose query")
            return
        query = sys.argv[2]
        search_files(query, verbose=True)

    elif command == "purge-batch":
        if len(sys.argv) != 3:
            print("Invalid arguments for purge-batch. Usage: fileindex.py purge-batch batch_id")
            return
        batch_id = sys.argv[2]
        purge_batch(batch_id)

    elif command == "archive-summary":
        get_archive_summary()

    elif command == "batch-summary":
        get_batch_summary()

    else:
        print("Invalid command.")

    # Close the database connection
    cursor.close()
    conn.close()

# Run the script
if __name__ == '__main__':
    main()
