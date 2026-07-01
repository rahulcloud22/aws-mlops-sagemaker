# # Data Preprocessing
# * Lower Case
# * Tokenization
# * Removing Special Characters
# * Removing stop words and punctuation
# * Stemming

import argparse
import pandas as pd
import os
import nltk
import string

from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

from nltk.corpus import stopwords
stopwords.words('english')

from nltk.stem.porter import PorterStemmer
ps = PorterStemmer()

from sklearn.model_selection import train_test_split

def transorm_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    y= []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        if i not in stopwords.words('english') and i not in string.punctuation:
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))

    return " ".join(y)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str)
    parser.add_argument("--output-path", type=str)
    args = parser.parse_args()

    print("Reading CSV from:", args.input_path)
    df = pd.read_csv(args.input_path, engine='python', encoding='utf-8')

    # Example preprocessing:
    print(df.shape)
    df.drop(columns=['Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4'], inplace=True)
    df.rename(columns={'v1':'target', 'v2':'message'}, inplace=True)
    df["target"] = encoder.fit_transform(df['target'])
    df.duplicated().sum()
    df = df.drop_duplicates(keep='first')
    df['target'].value_counts()
    df["transformed_text"] = df['message'].apply(transorm_text)
    print(df.shape)
    print("Reading CSV completed.")
    df.sample(5)

    
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

    os.makedirs(f"{args.output_path}/train", exist_ok=True)
    output_file = os.path.join(args.output_path, "train/train.csv")
    train_df.to_csv(output_file, index=False)
    print("Saved processed file to:", output_file)

    
    os.makedirs(f"{args.output_path}/test", exist_ok=True)
    output_file = os.path.join(args.output_path, "test/test.csv")
    test_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()