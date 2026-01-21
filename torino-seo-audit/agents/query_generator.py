"""
Query Generator Agent
Genera query di ricerca simulate da turisti italiani/francesi/inglesi
interessati a eventi a Torino e Piemonte.
"""

import os
from typing import List, Dict
import json
from openai import OpenAI


class QueryGeneratorAgent:
    """Agent che genera query di ricerca simulate usando LLM."""
    
    def __init__(self, api_key: str = None):
        """
        Inizializza l'agent con API key OpenAI.
        
        Args:
            api_key: OpenAI API key. Se None, usa variabile ambiente OPENAI_API_KEY
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key non trovata. Imposta OPENAI_API_KEY.")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_queries(
        self, 
        num_queries: int = 100,
        languages: List[str] = None,
        topics: List[str] = None
    ) -> List[Dict[str, str]]:
        """
        Genera query di ricerca simulate.
        
        Args:
            num_queries: Numero totale di query da generare (default: 100)
            languages: Liste di lingue (default: ['it', 'fr', 'en'])
            topics: Lista di topic (default: eventi, attrazioni, ristoranti, ecc.)
        
        Returns:
            Lista di dizionari con {query, language, location, intent}
        """
        if languages is None:
            languages = ['it', 'fr', 'en']
        
        if topics is None:
            topics = [
                'eventi culturali',
                'concerti e musica',
                'mostre e musei',
                'festival',
                'ristoranti e cucina locale',
                'attrazioni turistiche',
                'attività sportive',
                'vita notturna',
                'shopping',
                'tour guidati'
            ]
        
        # Data corrente per contesto temporale
        current_date = "gennaio 2026"
        current_season = "inverno 2025/26"
        
        prompt = f"""Sei un esperto di turismo e SEO. Oggi siamo a {current_date}.

Genera {num_queries} query di ricerca realistiche che turisti di diverse nazionalità 
(italiano, francese, inglese) potrebbero fare su Google quando cercano informazioni 
su eventi, attrazioni e attività a Torino e Piemonte.

IMPORTANTE - Riferimenti temporali:
- Se includi date/periodi, usa SOLO: "{current_date}", "{current_season}", "questo weekend", "febbraio 2026", "primavera 2026"
- NON usare date passate come 2023, 2024
- Preferisci query senza date specifiche o con "oggi", "questo weekend", "ora"

Le query devono essere:
- Diverse tra loro (varietà di formulazione, lunghezza, intento)
- Realistiche (come cercherebbe davvero un turista)
- Bilanciate tra le lingue: italiano, francese, inglese
- Coprire diversi topic: {', '.join(topics)}
- Includere varianti long-tail e short-tail
- Includere query informazionali, navigazionali e transazionali

Fornisci il risultato in formato JSON come array di oggetti con questa struttura:
{{
    "query": "la query di ricerca esatta",
    "language": "it|fr|en",
    "location": "Torino|Piemonte|Turin|Piedmont|...",
    "intent": "informational|navigational|transactional",
    "topic": "uno dei topic"
}}

Genera esattamente {num_queries} query diverse e creative."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modello economico: 20x più economico di GPT-4o
                messages=[
                    {"role": "system", "content": "Sei un esperto di turismo e SEO che genera query di ricerca realistiche."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,  # Alta creatività per maggiore varietà
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Estrai l'array di query (potrebbe essere in 'queries' o altri nomi)
            if 'queries' in result:
                queries = result['queries']
            elif 'results' in result:
                queries = result['results']
            elif isinstance(result, list):
                queries = result
            else:
                # Se è un oggetto con chiavi, prendi il primo valore che è una lista
                for value in result.values():
                    if isinstance(value, list):
                        queries = value
                        break
                else:
                    queries = []
            
            print(f"✓ Generate {len(queries)} query di ricerca")
            return queries
            
        except Exception as e:
            print(f"✗ Errore nella generazione query: {e}")
            return []
    
    def save_queries(self, queries: List[Dict[str, str]], filepath: str):
        """Salva le query generate in un file JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(queries, f, ensure_ascii=False, indent=2)
        print(f"✓ Query salvate in {filepath}")


if __name__ == "__main__":
    # Test del generatore
    generator = QueryGeneratorAgent()
    queries = generator.generate_queries(num_queries=20)
    
    print("\n--- Esempi di query generate ---")
    for i, q in enumerate(queries[:5], 1):
        print(f"{i}. [{q.get('language', 'N/A')}] {q.get('query', 'N/A')} ({q.get('intent', 'N/A')})")
    
    generator.save_queries(queries, "data/generated_queries.json")
