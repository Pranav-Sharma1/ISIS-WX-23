files = glob.glob("BLM_R5IM_Data/cycle" + '/*.csv')
selected_file = files[0]  
input_data = pd.read_csv(selected_file)
dataframe = input_data.drop(columns = input_data.columns[0]).to_numpy()
