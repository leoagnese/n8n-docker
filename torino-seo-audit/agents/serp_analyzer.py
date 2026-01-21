"""
SERP Analyzer Agent
Analizza i risultati SERP estratti per costruire un audit SEO/geo completo.
"""

import os
import json
from typing import List, Dict, Any
from collections import defaultdict, Counter
from datetime import datetime
from openai import OpenAI
from urllib.parse import urlparse


class SerpAnalyzerAgent:
    """Agent che analizza risultati SERP per audit SEO/geo."""
    
    def __init__(self, api_key: str = None):
        """
        Inizializza l'analyzer con API key OpenAI.
        
        Args:
            api_key: OpenAI API key. Se None, usa variabile ambiente OPENAI_API_KEY
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key non trovata. Imposta OPENAI_API_KEY.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.target_brand = "Turismo Torino"
    
    def analyze_serp_batch(self, serp_results: List[Dict]) -> Dict[str, Any]:
        """
        Analizza un batch di risultati SERP.
        
        Args:
            serp_results: Lista di risultati SERP estratti
        
        Returns:
            Dizionario con l'audit completo
        """
        print(f"\n=== Inizio Analisi SERP ({len(serp_results)} query) ===\n")
        
        audit = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(serp_results),
                "target_brand": self.target_brand
            },
            "brand_visibility": self._analyze_brand_visibility(serp_results),
            "competitor_analysis": self._analyze_competitors(serp_results),
            "geo_analysis": self._analyze_geo_distribution(serp_results),
            "content_insights": self._analyze_content_insights(serp_results),
            "serp_features": self._analyze_serp_features(serp_results),
            "ai_insights": self._generate_ai_insights(serp_results)
        }
        
        print("\n=== Analisi Completata ===\n")
        return audit
    
    def _analyze_brand_visibility(self, serp_results: List[Dict]) -> Dict:
        """Analizza la visibilità del brand Turismo Torino."""
        print("→ Analisi visibilità brand...")
        
        visibility = {
            "total_appearances": 0,
            "queries_with_brand": 0,
            "average_position": [],
            "top_3_appearances": 0,
            "top_10_appearances": 0,
            "urls_found": [],
            "by_language": defaultdict(int),
            "by_intent": defaultdict(int)
        }
        
        brand_keywords = ["turismo torino", "turismoTorino", "turismotorino"]
        
        for serp in serp_results:
            found_in_query = False
            query_meta = serp.get("query_metadata", {})
            language = query_meta.get("language", "unknown")
            intent = query_meta.get("intent", "unknown")
            
            for result in serp.get("organic_results", []):
                title = (result.get("title") or "").lower()
                link = result.get("link", "").lower()
                snippet = (result.get("snippet") or "").lower()
                displayed_link = (result.get("displayed_link") or "").lower()
                
                # Verifica se il brand è presente
                is_brand = any(brand in title or brand in link or brand in snippet or brand in displayed_link 
                              for brand in brand_keywords)
                
                if is_brand:
                    visibility["total_appearances"] += 1
                    found_in_query = True
                    position = result.get("position", 999)
                    visibility["average_position"].append(position)
                    
                    if position <= 3:
                        visibility["top_3_appearances"] += 1
                    if position <= 10:
                        visibility["top_10_appearances"] += 1
                    
                    if result.get("link"):
                        visibility["urls_found"].append({
                            "url": result["link"],
                            "query": serp["query"],
                            "position": position
                        })
                    
                    visibility["by_language"][language] += 1
                    visibility["by_intent"][intent] += 1
            
            if found_in_query:
                visibility["queries_with_brand"] += 1
        
        # Calcola posizione media
        if visibility["average_position"]:
            visibility["average_position_value"] = sum(visibility["average_position"]) / len(visibility["average_position"])
        else:
            visibility["average_position_value"] = None
        
        # Converti defaultdict in dict normale
        visibility["by_language"] = dict(visibility["by_language"])
        visibility["by_intent"] = dict(visibility["by_intent"])
        
        print(f"  ✓ Brand trovato in {visibility['queries_with_brand']}/{len(serp_results)} query")
        print(f"  ✓ {visibility['total_appearances']} apparizioni totali")
        print(f"  ✓ Posizione media: {visibility['average_position_value']:.1f}" if visibility["average_position_value"] else "  - Nessuna apparizione")
        
        return visibility
    
    def _analyze_competitors(self, serp_results: List[Dict]) -> Dict:
        """Analizza i competitor presenti nei risultati."""
        print("→ Analisi competitor...")
        
        domain_counter = Counter()
        domain_positions = defaultdict(list)
        
        for serp in serp_results:
            for result in serp.get("organic_results", []):
                link = result.get("link", "")
                if link:
                    domain = urlparse(link).netloc
                    domain_counter[domain] += 1
                    domain_positions[domain].append(result.get("position", 999))
        
        # Top 20 competitor
        top_competitors = []
        for domain, count in domain_counter.most_common(20):
            positions = domain_positions[domain]
            top_competitors.append({
                "domain": domain,
                "appearances": count,
                "average_position": sum(positions) / len(positions),
                "best_position": min(positions),
                "worst_position": max(positions)
            })
        
        print(f"  ✓ Trovati {len(domain_counter)} domini unici")
        print(f"  ✓ Top 3 competitor: {', '.join([c['domain'] for c in top_competitors[:3]])}")
        
        return {
            "total_unique_domains": len(domain_counter),
            "top_competitors": top_competitors
        }
    
    def _analyze_geo_distribution(self, serp_results: List[Dict]) -> Dict:
        """Analizza la distribuzione geografica dei risultati."""
        print("→ Analisi distribuzione geografica...")
        
        geo_stats = {
            "by_language": defaultdict(int),
            "by_location": defaultdict(int),
            "language_performance": {}
        }
        
        for serp in serp_results:
            language = serp.get("language", "unknown")
            location = serp.get("location", "unknown")
            
            geo_stats["by_language"][language] += 1
            geo_stats["by_location"][location] += 1
        
        # Converti in dict normale
        geo_stats["by_language"] = dict(geo_stats["by_language"])
        geo_stats["by_location"] = dict(geo_stats["by_location"])
        
        print(f"  ✓ Analizzate {len(geo_stats['by_language'])} lingue")
        print(f"  ✓ Analizzate {len(geo_stats['by_location'])} località")
        
        return geo_stats
    
    def _analyze_content_insights(self, serp_results: List[Dict]) -> Dict:
        """Analizza insights sui contenuti."""
        print("→ Analisi contenuti...")
        
        insights = {
            "common_keywords": [],
            "related_searches_all": [],
            "people_also_ask_all": []
        }
        
        # Raccogli tutte le ricerche correlate
        for serp in serp_results:
            for related in serp.get("related_searches", []):
                insights["related_searches_all"].append(related.get("query"))
            
            for paa in serp.get("people_also_ask", []):
                insights["people_also_ask_all"].append(paa.get("question"))
        
        # Trova le più comuni
        if insights["related_searches_all"]:
            related_counter = Counter(insights["related_searches_all"])
            insights["top_related_searches"] = [
                {"query": q, "count": c} 
                for q, c in related_counter.most_common(20)
            ]
        
        if insights["people_also_ask_all"]:
            paa_counter = Counter(insights["people_also_ask_all"])
            insights["top_questions"] = [
                {"question": q, "count": c} 
                for q, c in paa_counter.most_common(20)
            ]
        
        print(f"  ✓ Trovate {len(insights['related_searches_all'])} ricerche correlate")
        print(f"  ✓ Trovate {len(insights['people_also_ask_all'])} domande PAA")
        
        return insights
    
    def _analyze_serp_features(self, serp_results: List[Dict]) -> Dict:
        """Analizza le feature SERP presenti."""
        print("→ Analisi feature SERP...")
        
        features = {
            "knowledge_graph_count": 0,
            "related_searches_count": 0,
            "people_also_ask_count": 0,
            "rich_snippets_count": 0
        }
        
        for serp in serp_results:
            if serp.get("knowledge_graph"):
                features["knowledge_graph_count"] += 1
            
            if serp.get("related_searches"):
                features["related_searches_count"] += 1
            
            if serp.get("people_also_ask"):
                features["people_also_ask_count"] += 1
            
            for result in serp.get("organic_results", []):
                if result.get("rich_snippet"):
                    features["rich_snippets_count"] += 1
        
        print(f"  ✓ Knowledge Graph: {features['knowledge_graph_count']} volte")
        print(f"  ✓ Rich Snippets: {features['rich_snippets_count']} volte")
        
        return features
    
    def _generate_ai_insights(self, serp_results: List[Dict]) -> Dict:
        """Genera insights avanzati usando LLM."""
        print("→ Generazione insights AI (può richiedere tempo)...")
        
        # Prepara un sample di dati per l'analisi AI
        sample_data = {
            "total_queries": len(serp_results),
            "sample_queries": [s["query"] for s in serp_results[:10]],
            "sample_top_results": []
        }
        
        # Prendi i primi 3 risultati di alcune query
        for serp in serp_results[:5]:
            query_sample = {
                "query": serp["query"],
                "language": serp.get("language"),
                "top_3_titles": [r.get("title") for r in serp.get("organic_results", [])[:3]]
            }
            sample_data["sample_top_results"].append(query_sample)
        
        prompt = f"""Analizza questi dati SERP estratti da Google per query turistiche su Torino/Piemonte.

Dati:
{json.dumps(sample_data, ensure_ascii=False, indent=2)}

Target brand da analizzare: "{self.target_brand}"

Fornisci un'analisi strategica in formato JSON con:
1. "visibility_assessment": Valutazione della visibilità del brand (presente/assente/scarsa/buona/ottima)
2. "seo_opportunities": Array di 5-7 opportunità SEO concrete e actionable
3. "content_gaps": Array di 3-5 gap di contenuto da colmare
4. "strategic_recommendations": Array di 5-7 raccomandazioni strategiche prioritizzate
5. "competitive_threats": Array di 3-5 minacce competitive identificate

Rispondi solo con JSON valido."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modello economico: 20x più economico di GPT-4o
                messages=[
                    {"role": "system", "content": "Sei un esperto SEO e digital marketing specialist specializzato in analisi competitive e audit SEO."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            insights = json.loads(response.choices[0].message.content)
            print(f"  ✓ Insights AI generati")
            return insights
            
        except Exception as e:
            print(f"  ✗ Errore generazione insights AI: {e}")
            return {"error": str(e)}
    
    def save_audit(self, audit: Dict, filepath: str):
        """Salva l'audit in un file JSON."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(audit, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Audit salvato in {filepath}")
    
    def generate_report_html(self, audit: Dict, filepath: str):
        """Genera un report HTML leggibile."""
        print("→ Generazione report HTML...")
        
        # Calcola valori formattati
        avg_position = audit['brand_visibility']['average_position_value']
        avg_position_str = f"{avg_position:.1f}" if avg_position else "N/A"
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Audit - {audit['metadata']['target_brand']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .metadata {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .metric {{
            display: inline-block;
            background: #f8f9fa;
            padding: 20px 30px;
            margin: 10px 10px 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .recommendation {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .opportunity {{
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .alert {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SEO & Geo Audit Report</h1>
        <div class="metadata">
            <strong>Target:</strong> {audit['metadata']['target_brand']}<br>
            <strong>Data:</strong> {audit['metadata']['timestamp']}<br>
            <strong>Query Analizzate:</strong> {audit['metadata']['total_queries']}
        </div>
    </div>

    <div class="section">
        <h2>📊 Visibilità Brand</h2>
        <div class="metric">
            <div class="metric-value">{audit['brand_visibility']['queries_with_brand']}/{audit['metadata']['total_queries']}</div>
            <div class="metric-label">Query con Brand</div>
        </div>
        <div class="metric">
            <div class="metric-value">{audit['brand_visibility']['total_appearances']}</div>
            <div class="metric-label">Apparizioni Totali</div>
        </div>
        <div class="metric">
            <div class="metric-value">{avg_position_str}</div>
            <div class="metric-label">Posizione Media</div>
        </div>
        <div class="metric">
            <div class="metric-value">{audit['brand_visibility']['top_3_appearances']}</div>
            <div class="metric-label">Top 3 Posizioni</div>
        </div>
    </div>

    <div class="section">
        <h2>🌍 Distribuzione Geografica</h2>
        <table>
            <tr>
                <th>Lingua</th>
                <th>Query Analizzate</th>
            </tr>
"""
        
        for lang, count in audit['geo_analysis']['by_language'].items():
            html += f"""            <tr>
                <td>{lang.upper()}</td>
                <td>{count}</td>
            </tr>
"""
        
        html += """        </table>
    </div>

    <div class="section">
        <h2>🏆 Top Competitor</h2>
        <table>
            <tr>
                <th>Dominio</th>
                <th>Apparizioni</th>
                <th>Posizione Media</th>
                <th>Best Position</th>
            </tr>
"""
        
        for comp in audit['competitor_analysis']['top_competitors'][:10]:
            html += f"""            <tr>
                <td>{comp['domain']}</td>
                <td>{comp['appearances']}</td>
                <td>{comp['average_position']:.1f}</td>
                <td>{comp['best_position']}</td>
            </tr>
"""
        
        html += """        </table>
    </div>
"""
        
        # AI Insights
        if 'ai_insights' in audit and 'strategic_recommendations' in audit['ai_insights']:
            html += """    <div class="section">
        <h2>🤖 Raccomandazioni Strategiche AI</h2>
"""
            for rec in audit['ai_insights']['strategic_recommendations']:
                html += f"""        <div class="recommendation">
            {rec}
        </div>
"""
            html += """    </div>
"""
        
        if 'ai_insights' in audit and 'seo_opportunities' in audit['ai_insights']:
            html += """    <div class="section">
        <h2>💡 Opportunità SEO</h2>
"""
            for opp in audit['ai_insights']['seo_opportunities']:
                html += f"""        <div class="opportunity">
            {opp}
        </div>
"""
            html += """    </div>
"""
        
        html += """</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Report HTML salvato in {filepath}")


if __name__ == "__main__":
    # Test dell'analyzer
    analyzer = SerpAnalyzerAgent()
    
    # Carica risultati di test (se disponibili)
    test_file = "data/serp_results.json"
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            serp_results = json.load(f)
        
        audit = analyzer.analyze_serp_batch(serp_results)
        analyzer.save_audit(audit, "reports/audit.json")
        analyzer.generate_report_html(audit, "reports/audit.html")
    else:
        print(f"File {test_file} non trovato. Esegui prima l'estrazione SERP.")
