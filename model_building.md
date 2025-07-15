# Introduction to Sentiment Analysis

Sentiment analysis is the popular classification technique of determining attidues around a subject, entity, or event from natural language. The method and techniques of implementing sentiment analysis are long and well-documented from "simple" and inuitive models such as logistic regression and Naive Bayes Classifier and training models using a collection of vocabulary words (Bag of Words) to highly sophisticated and state of the art large language/reasoning models such as GPT-4, o4, BERT, Claude Opus 4 trained on large corpus of text throught the use of embeding layers that preserve word order, sentiment analysis seems to be a persistent and well researched topic surrounding these forementioned methods of prediction.


### Sentiment Analysis Using BERT
Improvements in the sophistication of models with the rise of attention based architecture have significantly improved performance of sentiment analysis over previous models such as recurrent neural networks or convolution neural networks due to the positional embeddings the model learns through pre-training and transformers ability to process whole sentences rather than word for word. The downside to the transformer model is its use of massive datasets and heavy computation costs. However, we overcome the limitation of pretraining BERT on the standard Wikipedia and Book corpora by using the pretrained BERT from the Huggingface library.

### Further Pretraining = Improved Results?
Text in financial data is notoriously tricky to detect sentiment due to the unique vocabulary and the lack of proper and labeled data make applying sentiment analysis difficult. This is where FinBERT comes in. FinBERT is a variation of BERT desinged specifically for application in the financial domain by using a method known as "further pre-training" which is training a BERT model on domain relevant corpa using the same training methods (masked language modeling and next sentence prediction) done during the training on the Wikipedia and BookCourpa corpora.
The authors of FinBERT decided to use Reuters TRC2 dataset and then filtering down to financial news articles for the pretraining of BERT; the idea of the pretraining is that it allows BERT to adjust its positional embeddings before it is fine-tuned on domain-specific dataset. 

After pretraining, FinBERT was then fine-tuned on the Financial Phrasebank dataset where it proved noticeable improvements over a standard BERT, ELmO, and (I forgot the last one). The result of this further pretraining demostrated the effectiveness and possibility of making better, domain-specific models for the purpose of sentiment analysis.

# Why FinBERT 2?
The original FinBERT model was made in 2019. Since then with a substantial rise of retail investors [link here], the COVID-19 pandemic, and the impact of Artifical Intelligence, rising interest rates have made both changes in the way we communicate and the way markets, particularly stock markets, operate in higher volatility enviroment. 

It is my personal belief that the change in enviroment should be reflected in the data we use to train our LLMs, this to me, is particularly important when it comes to training LLMs on domain specific tasks.

For that reason, the data we collect and use to train FinBERT 2 should reflect my sentiment. Ideally, we want a LLM that is knowledgeable on financial vocabulary and news but is also an excellent room reader and can understand the anger/frustration/skepticism traders may have towards a stock.

# Collecting Datasets

## Model Training and Data Colletion
For the pretraining, we'll be using Huggingface extensively as it offers a variety of benefits when it comes to training LLMs. Using HuggingFace gives us access to a variety of large datasets perfect for training LLMs and are easy to access using the HuggingFace API in Python. HuggingFace also allows for me store up to 100gb that can be used to store tokenized datasets so they don't have to be loaded in locally. Most importantly, as noted earlier, HuggingFace provides easy access to the BERT model that is already pretrained on the Wikipedia and BookCorpus corpora along with the functions necessary to carry out the further pretraining. 

## Data Accessing
To access the Huggingface datasets, we'll be using PySpark over popular alternatives such as Pandas. The reason for this is that if we wanted to increase the number of datasets to manage, PySpark would easily be able to handle the processing and loading required by the data.



## Data Collection
For further pretraining, the two datasets we'll look to use are the [Reuteurs Financial Dataset](https://huggingface.co/datasets/danidanou/Reuters_Financial_News) that records Reuteurs Financial news artciles from 2006-2013 and this corpora of [Financial News Articles](https://huggingface.co/datasets/ashraq/financial-news-articles) from seemingly 2017-2018. Finally, we'll use the [FinTwit dataset](https://huggingface.co/datasets/StephanAkkerman/financial-tweets).