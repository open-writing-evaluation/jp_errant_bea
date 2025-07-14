from importlib import import_module
import json
import stanza
from jp_errant.annotator import Annotator

# ERRANT version
__version__ = '3.0.1'

# Load an ERRANT Annotator object for a given language
def load(lang, nlp=None, legacy=True, use_gpu=True):
    # Make sure the language is supported
    if legacy:
        supported = {"en", "ko", "zh", "de", "uk", "cs"}
        if lang not in supported:
            raise ValueError(f"{lang} is an unsupported or unknown language")

        # Load Stanza pipeline
        if lang=="en":
            nlp = nlp or stanza.Pipeline(lang, processors="tokenize,pos,mwt,lemma,depparse") # optimize for faster performace
        elif lang in ["de", "uk", "cs"]:
            nlp = nlp or stanza.Pipeline(lang, processors="tokenize,pos,mwt,lemma,depparse") 
        elif lang=="zh":
            SAVED_MODEL_FOLDER = "./trained_models/"  # point to the folder with save pt files
            # Define paths for all custom models
            tokenize_path = SAVED_MODEL_FOLDER + "UD_Chinese-GSDSimpLTP_model/saved_models/tokenize/zh_gsdsimpltp_tokenizer.pt"
            pos_path = SAVED_MODEL_FOLDER + "UD_Chinese-GSDSimpLTP_model/saved_models/pos/zh_gsdsimpltp_nocharlm_tagger.pt"
            lemma_path = SAVED_MODEL_FOLDER + "UD_Chinese-GSDSimpLTP_model/saved_models/lemma/zh_gsdsimpltp_nocharlm_lemmatizer.pt"
            
            nlp = stanza.Pipeline(
                lang="zh",
                processors="tokenize,pos,lemma,depparse",
                # tokenize_model_path=tokenize_path,
                # pos_model_path=pos_path,
                # lemma_model_path=lemma_path
            )

            #nlp = nlp or stanza.Pipeline(lang, processors="tokenize,pos,lemma,depparse") # optimize for faster performace
        else:
            nlp = nlp or stanza.Pipeline(lang) 
            

        
        # Load language edit merger
        merger = import_module(f"jp_errant.{lang}.merger")

        # Load language edit classifier
        classifier = import_module(f"jp_errant.{lang}.classifier")
        classifier.nlp = nlp
    else:
        with open("jp_errant/stanza_resources_1.7.0.json", mode='r', encoding='utf-8') as f:
            stanza_supported = json.load(f).keys()
        
        if lang not in stanza_supported:
            raise ValueError(f"{lang} is an unsupported or unknown language")
        
        if lang=="en":
            nlp = nlp or stanza.Pipeline(lang, processors="tokenize,pos,mwt,lemma,depparse") # optimize for faster performace
        elif lang=="zh":
            nlp = nlp or stanza.Pipeline(lang, processors="tokenize,pos,lemma,depparse") # optimize for faster performace
        else:
            nlp = nlp or stanza.Pipeline(lang) 

        merger = import_module(f"jp_errant.multi.merger")
        classifier = import_module(f"jp_errant.multi.classifier")
        classifier.nlp = nlp

    # Return a configured ERRANT annotator
    return Annotator(lang, nlp, merger, classifier)
