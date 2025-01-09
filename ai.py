from transformers import pipeline

summary_input = f"Say Hi"
summary = summarizer(summary_input, max_length=13, min_length=6, do_sample=False)
print(summary[0]['summary_text'])