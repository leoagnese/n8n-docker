"""
Main Orchestrator
Coordina tutti gli agent per eseguire l'audit SEO/geo completo.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente dal file .env
load_dotenv()

# Importa gli agent
from agents.query_generator import QueryGeneratorAgent
from agents.serp_extractor import SerpExtractor
from agents.serp_analyzer import SerpAnalyzerAgent


class TorinoSEOAudit:
    """Orchestratore principale per l'audit SEO/geo di Turismo Torino."""
    
    def __init__(self):
        """Inizializza l'orchestratore."""
        self.data_dir = Path("data")
        self.reports_dir = Path("reports")
        
        # Crea le directory se non esistono
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Inizializza gli agent
        print("=== Inizializzazione Agent ===\n")
        
        try:
            self.query_generator = QueryGeneratorAgent()
            print("✓ Query Generator Agent inizializzato")
        except ValueError as e:
            print(f"✗ Errore Query Generator: {e}")
            sys.exit(1)
        
        try:
            self.serp_extractor = SerpExtractor()
            print("✓ SERP Extractor inizializzato")
        except ValueError as e:
            print(f"✗ Errore SERP Extractor: {e}")
            sys.exit(1)
        
        try:
            self.serp_analyzer = SerpAnalyzerAgent()
            print("✓ SERP Analyzer Agent inizializzato")
        except ValueError as e:
            print(f"✗ Errore SERP Analyzer: {e}")
            sys.exit(1)
        
        print("\n✓ Tutti gli agent sono pronti!\n")
    
    def run_full_audit(
        self, 
        num_queries: int = 50,
        serp_delay: float = 1.0,
        skip_query_generation: bool = False,
        skip_serp_extraction: bool = False
    ):
        """
        Esegue l'audit completo: generazione query -> estrazione SERP -> analisi.
        
        Args:
            num_queries: Numero di query da generare
            serp_delay: Delay tra richieste SERP (secondi)
            skip_query_generation: Se True, usa query già generate
            skip_serp_extraction: Se True, usa SERP già estratte
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Percorsi file
        queries_file = self.data_dir / f"queries_{timestamp}.json"
        serp_file = self.data_dir / f"serp_results_{timestamp}.json"
        audit_file = self.reports_dir / f"audit_{timestamp}.json"
        report_file = self.reports_dir / f"audit_{timestamp}.html"
        
        # STEP 1: Generazione Query
        if not skip_query_generation:
            print("\n" + "="*60)
            print("STEP 1: Generazione Query Simulate")
            print("="*60 + "\n")
            
            queries = self.query_generator.generate_queries(
                num_queries=num_queries,
                languages=['it', 'fr', 'en']
            )
            
            if not queries:
                print("✗ Nessuna query generata. Interruzione.")
                return
            
            self.query_generator.save_queries(queries, str(queries_file))
            print(f"\n✓ {len(queries)} query generate e salvate\n")
        else:
            print("\n→ Skip generazione query (usando file esistente)")
            # Trova il file più recente
            query_files = sorted(self.data_dir.glob("queries_*.json"), reverse=True)
            if not query_files:
                print("✗ Nessun file query trovato. Genera prima le query.")
                return
            queries_file = query_files[0]
            with open(queries_file, 'r', encoding='utf-8') as f:
                queries = json.load(f)
            print(f"✓ Caricate {len(queries)} query da {queries_file.name}\n")
        
        # STEP 2: Estrazione SERP
        if not skip_serp_extraction:
            print("\n" + "="*60)
            print("STEP 2: Estrazione Risultati SERP")
            print("="*60 + "\n")
            print(f"⚠️  Questo richiederà circa {len(queries) * serp_delay / 60:.1f} minuti")
            print(f"    ({len(queries)} query × {serp_delay}s delay)\n")
            
            serp_results = self.serp_extractor.extract_batch(
                queries=queries,
                delay=serp_delay,
                save_progress=True,
                output_file=str(serp_file)
            )
            
            if not serp_results:
                print("✗ Nessun risultato SERP estratto. Interruzione.")
                return
            
            print(f"\n✓ {len(serp_results)} SERP estratte e salvate\n")
        else:
            print("\n→ Skip estrazione SERP (usando file esistente)")
            # Trova il file più recente
            serp_files = sorted(self.data_dir.glob("serp_results_*.json"), reverse=True)
            if not serp_files:
                print("✗ Nessun file SERP trovato. Estrai prima le SERP.")
                return
            serp_file = serp_files[0]
            with open(serp_file, 'r', encoding='utf-8') as f:
                serp_results = json.load(f)
            print(f"✓ Caricati {len(serp_results)} risultati SERP da {serp_file.name}\n")
        
        # STEP 3: Analisi e Report
        print("\n" + "="*60)
        print("STEP 3: Analisi e Generazione Report")
        print("="*60 + "\n")
        
        audit = self.serp_analyzer.analyze_serp_batch(serp_results)
        
        # Salva l'audit
        self.serp_analyzer.save_audit(audit, str(audit_file))
        
        # Genera report HTML
        self.serp_analyzer.generate_report_html(audit, str(report_file))
        
        # Riepilogo finale
        print("\n" + "="*60)
        print("AUDIT COMPLETATO!")
        print("="*60 + "\n")
        
        print("📁 File generati:")
        print(f"  - Query: {queries_file}")
        print(f"  - SERP: {serp_file}")
        print(f"  - Audit JSON: {audit_file}")
        print(f"  - Report HTML: {report_file}")
        
        print("\n📊 Riepilogo:")
        print(f"  - Query analizzate: {audit['metadata']['total_queries']}")
        print(f"  - Brand visibility: {audit['brand_visibility']['queries_with_brand']}/{audit['metadata']['total_queries']} query")
        print(f"  - Posizione media brand: {audit['brand_visibility']['average_position_value']:.1f}" if audit['brand_visibility']['average_position_value'] else "  - Posizione media brand: N/A")
        print(f"  - Domini competitor: {audit['competitor_analysis']['total_unique_domains']}")
        
        print("\n🌐 Apri il report HTML per visualizzare l'analisi completa:")
        print(f"  {report_file.absolute()}")
        
        print("\n✓ Processo completato con successo!")


def main():
    """Funzione principale."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        TORINO SEO AUDIT - Turismo Torino                 ║
║        Analisi Visibilità Geo/SEO con Multi-Agent        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Verifica variabili d'ambiente
    print("→ Verifica configurazione...\n")
    
    required_env = {
        "OPENAI_API_KEY": "OpenAI API (per GPT)",
        "SERPAPI_KEY": "SerpAPI (per estrazione SERP)"
    }
    
    missing = []
    for key, desc in required_env.items():
        if os.getenv(key):
            print(f"  ✓ {desc}: configurata")
        else:
            print(f"  ✗ {desc}: MANCANTE")
            missing.append(key)
    
    if missing:
        print(f"\n⚠️  Configura le seguenti variabili d'ambiente:")
        for key in missing:
            print(f"   set {key}=<your-api-key>")
        print("\nOppure crea un file .env con le API key.")
        sys.exit(1)
    
    print("\n✓ Configurazione OK\n")
    
    # Crea l'orchestratore e avvia l'audit
    orchestrator = TorinoSEOAudit()
    
    # Configurazione audit
    # BUDGET LIMIT: $0.01 per sessione
    # Con GPT-4o-mini: 3 query (1 per lingua) = ~$0.002 (OpenAI) + $0 (SerpAPI free)
    # Report HTML per revisione con SEO e cliente (JSON per backup dati)
    
    num_queries = 3  # 1 query per lingua (IT, FR, EN) - test
    
    print("Configurazione audit:")
    print(f"  - Query da generare: {num_queries} (1 per lingua)")
    print("  - Modello LLM: GPT-4o-mini (economico)")
    print("  - Delay tra SERP: 1.0s")
    print("  - Lingue: IT, FR, EN")
    print(f"  - Output: Report HTML completo (priorità su JSON)")
    print(f"\n💰 Costo stimato: ~$0.002-0.003 (SOTTO BUDGET $0.01)")
    print(f"⏱️  Tempo stimato: ~30-45 secondi\n")
    print("→ Avvio audit...\n")
    
    orchestrator.run_full_audit(
        num_queries=num_queries,
        serp_delay=1.0,
        skip_query_generation=False,
        skip_serp_extraction=False
    )


if __name__ == "__main__":
    main()
