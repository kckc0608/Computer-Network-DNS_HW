def save_data_to_file(data, file_name):
    with open(file_name, 'a', encoding="utf-8") as file:
        file.write(data)