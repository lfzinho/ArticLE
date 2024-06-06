# ArticLE
A tool for parsing, searching and asking thorugh your own PDF folder of articles using search techniques and LLMs.

## Installation
Install the required packages:
```bash
pip install -r requirements.txt
```
Finally, create a `.env` file in the root directory of the project and add the API key for 
[OpenAI](https://beta.openai.com/signup/). The file should look like this:
```bash
OPENAI_API_KEY=your_api_key
```

## How to use
Run the following command to start the application:
```bash
python app/main.py
```
After that, open the file `index.html` in your browser. You can now search for articles and get summaries of them.
