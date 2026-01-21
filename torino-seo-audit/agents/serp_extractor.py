"""
SERP Extractor
Estrae risultati di ricerca da Google usando SerpAPI.
"""

import os
import time
from typing import List, Dict, Optional
import requests
import json


class SerpExtractor:
    """Estrae risultati SERP usando SerpAPI."""
    
    def __init__(self, api_key: str = None):
        """
        Inizializza l'extractor con SerpAPI key.
        
        Args:
            api_key: SerpAPI key. Se None, usa variabile ambiente SERPAPI_KEY
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SerpAPI key non trovata. Imposta SERPAPI_KEY.")
        
        self.base_url = "https://serpapi.com/search"
    
    def extract_serp(
        self, 
        query: str, 
        language: str = "it",
        location: str = "Italy",
        num_results: int = 10,
        max_retries: int = 3
    ) -> Dict:
        """
        Estrae risultati SERP per una query.
        
        Args:
            query: Query di ricerca
            language: Codice lingua (it, fr, en)
            location: Localizzazione geografica
            num_results: Numero di risultati da estrarre
            max_retries: Numero massimo di tentativi in caso di errore
        
        Returns:
            Dizionario con risultati SERP completi
        """
        # Mappa lingue a domini e parametri Google
        lang_config = {
            'it': {'google_domain': 'google.it', 'gl': 'it', 'hl': 'it', 'location': 'Italy'},
            'fr': {'google_domain': 'google.fr', 'gl': 'fr', 'hl': 'fr', 'location': 'France'},
            'en': {'google_domain': 'google.co.uk', 'gl': 'uk', 'hl': 'en', 'location': 'United Kingdom'}
        }
        
        config = lang_config.get(language, lang_config['it'])
        
        params = {
            "engine": "google",
            "q": query,
            "google_domain": config['google_domain'],
            "gl": config['gl'],
            "hl": config['hl'],
            "location": config.get('location', location),
            "num": num_results,
            "api_key": self.api_key
        }
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Estrai informazioni rilevanti
                result = {
                    "query": query,
                    "language": language,
                    "location": config.get('location', location),
                    "timestamp": time.time(),
                    "organic_results": [],
                    "related_searches": [],
                    "people_also_ask": [],
                    "knowledge_graph": None
                }
                
                # Risultati organici
                for item in data.get("organic_results", [])[:num_results]:
                    result["organic_results"].append({
                        "position": item.get("position"),
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "displayed_link": item.get("displayed_link"),
                        "snippet": item.get("snippet"),
                        "rich_snippet": item.get("rich_snippet"),
                        "sitelinks": item.get("sitelinks")
                    })
                
                # Ricerche correlate
                for item in data.get("related_searches", []):
                    result["related_searches"].append({
                        "query": item.get("query"),
                        "link": item.get("link")
                    })
                
                # People Also Ask
                for item in data.get("related_questions", []):
                    result["people_also_ask"].append({
                        "question": item.get("question"),
                        "snippet": item.get("snippet"),
                        "link": item.get("link")
                    })
                
                # Knowledge Graph
                if "knowledge_graph" in data:
                    kg = data["knowledge_graph"]
                    result["knowledge_graph"] = {
                        "title": kg.get("title"),
                        "type": kg.get("type"),
                        "description": kg.get("description"),
                        "source": kg.get("source")
                    }
                
                return result
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Tentativo {attempt + 1}/{max_retries} fallito, riprovo...")
                    time.sleep(2)  # Attendi prima di riprovare
                    continue
                else:
                    print(f"✗ Errore richiesta SerpAPI per '{query}': {e}")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Errore generico, riprovo (tentativo {attempt + 1}/{max_retries})...")
                    time.sleep(2)
                    continue
                else:
                    print(f"✗ Errore generico per '{query}': {e}")
                    return None
        
        return None
    
    def extract_batch(
        self, 
        queries: List[Dict[str, str]], 
        delay: float = 1.0,
        save_progress: bool = True,
        output_file: str = None
    ) -> List[Dict]:
        """
        Estrae SERP per un batch di query.
        
        Args:
            queries: Lista di query generate dall'agent
            delay: Delay tra richieste (secondi)
            save_progress: Salva progressi dopo ogni query
            output_file: File dove salvare i risultati
        
        Returns:
            Lista di risultati SERP
        """
        results = []
        total = len(queries)
        
        for i, query_info in enumerate(queries, 1):
            query = query_info.get("query", "")
            language = query_info.get("language", "it")
            
            print(f"[{i}/{total}] Estraendo SERP per: {query} ({language})")
            
            serp_data = self.extract_serp(
                query=query,
                language=language
            )
            
            if serp_data:
                # Aggiungi metadata dalla query originale
                serp_data["query_metadata"] = query_info
                results.append(serp_data)
                print(f"  ✓ Estratti {len(serp_data['organic_results'])} risultati organici")
            else:
                print(f"  ✗ Nessun risultato per questa query")
            
            # Salva progressi
            if save_progress and output_file and i % 10 == 0:
                self._save_results(results, output_file)
                print(f"  → Salvati progressi ({i}/{total})")
            
            # Delay per evitare rate limiting
            if i < total:
                time.sleep(delay)
        
        # Salvataggio finale
        if output_file:
            self._save_results(results, output_file)
            print(f"\n✓ Tutti i risultati salvati in {output_file}")
        
        return results
    
    def _save_results(self, results: List[Dict], filepath: str):
        """Salva i risultati in un file JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Test dell'extractor
    extractor = SerpExtractor()
    
    test_queries = [
        {"query": "eventi Torino oggi", "language": "it"},
        {"query": "things to do in Turin", "language": "en"},
        {"query": "événements Turin ce weekend", "language": "fr"}
    ]
    
    print("--- Test SerpAPI Extractor ---\n")
    results = extractor.extract_batch(test_queries, delay=2.0)
    
    print(f"\n✓ Estratti {len(results)} SERP")
    if results:
        print(f"\nEsempio primo risultato per '{results[0]['query']}':")
        if results[0]['organic_results']:
            print(f"  1. {results[0]['organic_results'][0]['title']}")
            print(f"     {results[0]['organic_results'][0]['link']}")
