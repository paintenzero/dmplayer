import uuid
import chromadb
from chromadb.utils import embedding_functions

class KnowledgeBase:
    def __init__(self, path: str, embedding_model: str, device: str):
        """
        Initialize and create chromadb
        """
        self.path = path
        self.embedding_model = embedding_model
        self.device = device
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model,
            device=device,
        )
        self.client = chromadb.PersistentClient(
            path=path,
            settings=chromadb.Settings(
                allow_reset=True
            )
        )
        self.documents = []
        self.ids = []
        self.metadatas = []

    def reset(self):
        """
        Reset current database
        """
        self.client.reset()

    def _add_embed_document(self, document: str, page: int, book_name: str):
        self.documents.append(document)
        self.ids.append(str(uuid.uuid4()))
        self.metadatas.append({
            'book': book_name,
            'page': page
        })
    
    def _reset_embed_documents(self):
        self.documents.clear()
        self.ids.clear()
        self.metadatas.clear()

    def embed(self, full_text, collection: str, book_name: str, chunk_sentences=10, overlap_sentences=5):
        """
        Embed the text and store in chromadb

        full_text - array of objects like {'page': <int>, 'text': 'line from the page'}
        collection - string - collection in database where to store the embeddings
        chuck_sentences - int - how many sentences to make in one chunk
        overlap_sentences - int - how many sentences to overlap between chunks
        """
        # Combine text into chunks of {chunk_sentences} sentences. 
        lines_cnt = len(full_text)
        i = 0
        while i < lines_cnt-1:
            line_strip = full_text[i]['text'].strip('\n ')
            while not line_strip.endswith(('.', '?', '!')) or len(line_strip.split('. ')) < chunk_sentences:
                if not line_strip.endswith('-'):
                    full_text[i]['text'] = line_strip + ' ' + full_text[i+1]['text'].strip()
                else:
                    full_text[i]['text'] = line_strip.rstrip('-') + full_text[i+1]['text'].strip()
                line_strip = full_text[i]['text'].strip('\n')
                full_text.pop(i+1)
                lines_cnt -= 1
                if i == lines_cnt - 1:
                    break
            i += 1

        # Create object for embedding and storing
        for i in range(0, len(full_text)):
            if i > 0:
                self._add_embed_document(
                    document='. '.join(full_text[i-1]['text'].split(". ")[-overlap_sentences:]) + "\n" + '. '.join(full_text[i]['text'].split(". ")[:overlap_sentences]),
                    page=full_text[i-1]['page'],
                    book_name=book_name
                )

            self._add_embed_document(
                document=full_text[i]['text'],
                page=full_text[i]['page'],
                book_name=book_name
            )

        print("Do embed and store in database")
        db_collection = self.client.get_or_create_collection(collection, embedding_function=self.sentence_transformer_ef)
        db_collection.add(
            documents=self.documents,
            ids=self.ids,
            metadatas=self.metadatas,
        )
        self._reset_embed_documents()


    def peek(self, collection: str):
        db_collection = self.client.get_or_create_collection(collection, embedding_function=self.sentence_transformer_ef)
        return db_collection.peek()


    def query(self, search: str, collection: str, n_results = 3):
        db_collection = self.client.get_or_create_collection(collection, embedding_function=self.sentence_transformer_ef)
        results = db_collection.query(
            query_texts=[search],
            n_results=n_results
        )
        return results