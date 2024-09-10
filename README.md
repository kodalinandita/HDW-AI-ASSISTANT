# HDW-AI-ASSISTANT
A speech and text compatible AI chat bot

## TO RUN AN INSTANCE

### Replace API key in line 14 with your own.
<img width="380" alt="image" src="https://github.com/user-attachments/assets/55080b85-7022-4f7f-8051-2f961c782369">

### Create a function to connect DB for users' personal queries
1. Username
2. Account Balance
3. Any other details you want the user to be able to access but make sure to modify the template (line 178 - 193) accordingly and include the 'if's' for it.

### Add more data for the chat bot to recognize
Add more files in the data folder for the program to feed them to the chat bot.

### In the terminal, type this command
'streamlit run main.py'

## IMPROVEMENTS TO BE MADE

### Improve UI interface

- Speech input: The messages are saved above the actual recording interface (which may or may not be ideal).
  <img width="775" alt="image" src="https://github.com/user-attachments/assets/1ec1580e-929e-4b5c-a709-c6d444f49f7b">

- Speech input: Change the icon for recording to a more intuitive design
  Not recording: <img width="727" alt="image" src="https://github.com/user-attachments/assets/d12f9dc7-e55f-4b91-a983-ec32741f1399">
  Recording: <img width="727" alt="image" src="https://github.com/user-attachments/assets/4ce0d967-d63a-47cf-922f-190b4a4a24ea">


### LLM inefficiency
- The LLM's are trained better in certain languages than others. English, Hindi, and Marathi are good. Rest are not as accurate. It would be ideal to find a good alternative LLM for those languages.

  Good response (Hindi):
  <img width="712" alt="image" src="https://github.com/user-attachments/assets/9740c413-59b0-4d2c-bbbd-d9bb018ee1fa">
  
  Bad response (Telugu): 
  <img width="710" alt="image" src="https://github.com/user-attachments/assets/451d4119-bf11-44fd-8850-e4ca28e4ded3">

- Sometimes the LLM's hallucinate and format answers in different ways. To fix this, I used chatGPT to create a prompt template which significantly reduced this issue. However, they still persist.
