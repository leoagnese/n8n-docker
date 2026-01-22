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
        """Genera una dashboard HTML moderna e professionale."""
        print("→ Generazione dashboard HTML...")
        
        import html as html_module
        
        # Calcola valori formattati
        avg_position = audit['brand_visibility']['average_position_value']
        avg_position_str = f"{avg_position:.1f}" if avg_position else "N/A"
        
        # Prepara dati SERP (assumendo che siano stati salvati nell'audit)
        serp_results = audit.get('_raw_serp_results', [])
        
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Dashboard - {audit['metadata']['target_brand']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        brand: '#667eea',
                        success: '#10b981',
                        warning: '#f59e0b',
                        danger: '#ef4444'
                    }}
                }}
            }}
        }}
    </script>
    <style>
        .card-hover {{ transition: transform 0.2s, box-shadow 0.2s; }}
        .card-hover:hover {{ transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }}
        .gradient-brand {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .tag {{ display: inline-block; padding: 0.25rem 0.75rem; margin: 0.25rem; border-radius: 9999px; font-size: 0.875rem; }}
        .accordion-content {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }}
        .accordion-content.active {{ max-height: 500px; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .fade-in {{ animation: fadeIn 0.5s ease-out; }}
    </style>
</head>
<body class="bg-gray-50 text-gray-900">
    <!-- Header -->
    <div class="gradient-brand text-white p-8 shadow-xl">
        <div class="max-w-7xl mx-auto">
            <h1 class="text-4xl font-bold mb-2">SEO & GEO Audit Dashboard</h1>
            <p class="text-lg opacity-90">
                <span class="font-semibold">{audit['metadata']['target_brand']}</span> · 
                {audit['metadata']['timestamp'][:10]} · 
                {audit['metadata']['total_queries']} query analizzate
            </p>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 py-8">
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 fade-in">
            <!-- Card 1: Brand Visibility -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="text-3xl">📊</div>
                    <div class="text-right">
                        <div class="text-3xl font-bold text-brand">{audit['brand_visibility']['queries_with_brand']}/{audit['metadata']['total_queries']}</div>
                        <div class="text-sm text-gray-600 mt-1">Query con Brand</div>
                    </div>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-brand h-2 rounded-full" style="width: {(audit['brand_visibility']['queries_with_brand']/audit['metadata']['total_queries']*100) if audit['metadata']['total_queries'] > 0 else 0}%"></div>
                </div>
            </div>

            <!-- Card 2: Average Position -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="text-3xl">🎯</div>
                    <div class="text-right">
                        <div class="text-3xl font-bold {'text-success' if avg_position and avg_position <= 3 else 'text-warning' if avg_position and avg_position <= 7 else 'text-danger'}">{avg_position_str}</div>
                        <div class="text-sm text-gray-600 mt-1">Posizione Media</div>
                    </div>
                </div>
                <div class="text-xs text-gray-500">Top 3: {audit['brand_visibility']['top_3_appearances']} apparizioni</div>
            </div>

            <!-- Card 3: Total Appearances -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="text-3xl">⚡</div>
                    <div class="text-right">
                        <div class="text-3xl font-bold text-brand">{audit['brand_visibility']['total_appearances']}</div>
                        <div class="text-sm text-gray-600 mt-1">Apparizioni Totali</div>
                    </div>
                </div>
                <div class="text-xs text-gray-500">Top 10: {audit['brand_visibility']['top_10_appearances']} volte</div>
            </div>

            <!-- Card 4: Competitors -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="text-3xl">🌍</div>
                    <div class="text-right">
                        <div class="text-3xl font-bold text-brand">{audit['competitor_analysis']['total_unique_domains']}</div>
                        <div class="text-sm text-gray-600 mt-1">Domini Competitor</div>
                    </div>
                </div>
                <div class="text-xs text-gray-500">{len(audit['geo_analysis']['by_language'])} lingue analizzate</div>
            </div>
        </div>

        <!-- SERP Visualization -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8 fade-in">
            <h2 class="text-2xl font-bold mb-6 text-brand flex items-center">
                <span class="mr-2">🔍</span> Risultati Organici SERP
            </h2>
            <div class="space-y-4">
"""
        
        # Mostra risultati organici per ogni query (prendendo dalle URLs trovate o dai competitor)
        position_colors = {
            1: 'border-yellow-400 bg-yellow-50',
            2: 'border-gray-400 bg-gray-50',
            3: 'border-orange-400 bg-orange-50'
        }
        
        # Top 10 competitor per mostrare i risultati
        top_results = audit['competitor_analysis']['top_competitors'][:10]
        for idx, comp in enumerate(top_results, 1):
            color_class = position_colors.get(comp['best_position'], 'border-gray-200 bg-white')
            is_brand = 'turismotorino' in comp['domain'].lower()
            badge_class = 'bg-success text-white' if is_brand else 'bg-gray-200 text-gray-700'
            
            html += f"""                <div class="border-l-4 {color_class} p-4 rounded-lg">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="text-lg font-bold text-gray-400">#{comp['best_position']}</span>
                                <span class="px-3 py-1 rounded-full text-xs font-semibold {badge_class}">
                                    {'✅ TARGET BRAND' if is_brand else comp['domain']}
                                </span>
                            </div>
                            <div class="text-sm text-gray-600 space-y-1">
                                <div>🌐 <span class="font-mono text-xs">{html_module.escape(comp['domain'])}</span></div>
                                <div>📊 Apparizioni: <span class="font-semibold">{comp['appearances']}</span> · Pos. media: <span class="font-semibold">{comp['average_position']:.1f}</span></div>
                            </div>
                        </div>
                    </div>
                </div>
"""
        
        html += """            </div>
        </div>

        <!-- Brand Status & SERP Features Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- Brand Status -->
            <div class="bg-white rounded-xl shadow-lg p-6 fade-in">
                <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                    <span class="mr-2">✅</span> Brand Status
                </h3>
"""
        
        if audit['brand_visibility']['queries_with_brand'] > 0:
            html += f"""                <div class="bg-green-50 border-l-4 border-success p-4 rounded mb-4">
                    <div class="font-bold text-success mb-2">PRESENTE</div>
                    <div class="text-sm text-gray-700">
                        📍 Posizione: <span class="font-bold">#{avg_position_str}</span><br>
                        📄 Apparizioni: <span class="font-bold">{audit['brand_visibility']['total_appearances']}</span>
                    </div>
                </div>
                
                <!-- Position Chart -->
                <div class="mt-4">
                    <div class="text-xs text-gray-600 mb-2">Distribuzione posizioni (1-10):</div>
                    <div class="flex gap-1">
"""
            for pos in range(1, 11):
                is_active = any(item.get('position') == pos for item in audit['brand_visibility']['urls_found'])
                html += f'                        <div class="flex-1 h-8 rounded {"bg-brand" if is_active else "bg-gray-200"} flex items-center justify-center text-xs text-white font-bold">{pos if is_active else ""}</div>\n'
            
            html += """                    </div>
                </div>
"""
        else:
            html += """                <div class="bg-red-50 border-l-4 border-danger p-4 rounded">
                    <div class="font-bold text-danger mb-2">❌ NON PRESENTE</div>
                    <div class="text-sm text-gray-700">Il brand non appare nei primi 10 risultati</div>
                </div>
"""
        
        html += """            </div>

            <!-- SERP Features -->
            <div class="bg-white rounded-xl shadow-lg p-6 fade-in">
                <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                    <span class="mr-2">📊</span> SERP Features
                </h3>
                <div class="space-y-3">
"""
        
        features = [
            ('✅' if audit['serp_features']['knowledge_graph_count'] > 0 else '❌', 'Knowledge Graph', f"{audit['serp_features']['knowledge_graph_count']}/{audit['metadata']['total_queries']} query"),
            ('✅' if audit['serp_features']['people_also_ask_count'] > 0 else '❌', 'People Also Ask', f"{audit['serp_features']['people_also_ask_count']}/{audit['metadata']['total_queries']} query"),
            ('✅' if audit['serp_features']['related_searches_count'] > 0 else '❌', 'Related Searches', f"{audit['serp_features']['related_searches_count']}/{audit['metadata']['total_queries']} query"),
            ('⚠️' if audit['serp_features']['rich_snippets_count'] > 0 else '❌', 'Rich Snippets', f"{audit['serp_features']['rich_snippets_count']} trovati"),
        ]
        
        for icon, name, value in features:
            html += f"""                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <span class="flex items-center gap-2"><span class="text-xl">{icon}</span> <span class="font-medium">{name}</span></span>
                        <span class="text-sm text-gray-600">{value}</span>
                    </div>
"""
        
        html += """                </div>
            </div>
        </div>

        <!-- People Also Ask Accordion -->
"""
        
        if audit['content_insights'].get('top_questions'):
            html += """        <div class="bg-white rounded-xl shadow-lg p-6 mb-8 fade-in">
            <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                <span class="mr-2">❓</span> People Also Ask
            </h3>
            <div class="space-y-2">
"""
            for idx, item in enumerate(audit['content_insights']['top_questions'][:8]):
                question = html_module.escape(item.get('question') or '')
                html += f"""                <div class="border border-gray-200 rounded-lg">
                    <button onclick="this.nextElementSibling.classList.toggle('active')" class="w-full text-left p-4 hover:bg-gray-50 flex items-center justify-between">
                        <span class="font-medium">{question}</span>
                        <span class="text-gray-400">▼</span>
                    </button>
                    <div class="accordion-content px-4 bg-gray-50">
                        <div class="py-3 text-sm text-gray-600">Frequenza: {item.get('count', 0)} volte</div>
                    </div>
                </div>
"""
            html += """            </div>
        </div>
"""
        
        # Related Searches Tag Cloud
        if audit['content_insights'].get('top_related_searches'):
            html += """        <div class="bg-white rounded-xl shadow-lg p-6 mb-8 fade-in">
            <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                <span class="mr-2">🔗</span> Related Searches
            </h3>
            <div class="flex flex-wrap gap-2">
"""
            for item in audit['content_insights']['top_related_searches'][:20]:
                query = html_module.escape(item.get('query') or '')
                html += f"""                <span class="tag bg-brand text-white">{query} <span class="opacity-75">({item.get('count', 0)})</span></span>
"""
            html += """            </div>
        </div>
"""
        
        # Competitor Analysis Table
        html += """        <div class="bg-white rounded-xl shadow-lg p-6 mb-8 fade-in">
            <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                <span class="mr-2">🏆</span> Analisi Competitor
            </h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="px-4 py-3 text-left font-semibold">Dominio</th>
                            <th class="px-4 py-3 text-center font-semibold">Apparizioni</th>
                            <th class="px-4 py-3 text-center font-semibold">Pos. Media</th>
                            <th class="px-4 py-3 text-center font-semibold">Migliore</th>
                            <th class="px-4 py-3 text-center font-semibold">Peggiore</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for comp in audit['competitor_analysis']['top_competitors'][:15]:
            is_brand = 'turismotorino' in comp['domain'].lower()
            row_class = 'bg-green-50 font-semibold' if is_brand else 'hover:bg-gray-50'
            html += f"""                        <tr class="{row_class}">
                            <td class="px-4 py-3 border-t">{html_module.escape(comp['domain'])} {'✅' if is_brand else ''}</td>
                            <td class="px-4 py-3 border-t text-center">{comp['appearances']}</td>
                            <td class="px-4 py-3 border-t text-center">{comp['average_position']:.1f}</td>
                            <td class="px-4 py-3 border-t text-center font-bold">#{comp['best_position']}</td>
                            <td class="px-4 py-3 border-t text-center">#{comp['worst_position']}</td>
                        </tr>
"""
        
        html += """                    </tbody>
                </table>
            </div>
        </div>

        <!-- Performance per Lingua & Intent -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- Performance Lingua -->
            <div class="bg-white rounded-xl shadow-lg p-6 fade-in">
                <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                    <span class="mr-2">🌍</span> Performance per Lingua
                </h3>
                <div class="space-y-3">
"""
        
        for lang, count in audit['geo_analysis']['by_language'].items():
            lang_upper = lang.upper()
            brand_count = audit['brand_visibility']['by_language'].get(lang, 0)
            percentage = (brand_count / count * 100) if count > 0 else 0
            html += f"""                    <div>
                        <div class="flex justify-between mb-1">
                            <span class="font-medium">{lang_upper}</span>
                            <span class="text-sm text-gray-600">{brand_count}/{count} query</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-brand h-2 rounded-full" style="width: {percentage}%"></div>
                        </div>
                    </div>
"""
        
        html += """                </div>
            </div>

            <!-- Performance Intent -->
            <div class="bg-white rounded-xl shadow-lg p-6 fade-in">
                <h3 class="text-xl font-bold mb-4 text-brand flex items-center">
                    <span class="mr-2">🎯</span> Performance per Intent
                </h3>
                <div class="space-y-3">
"""
        
        for intent, count in audit['brand_visibility']['by_intent'].items():
            html += f"""                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                        <span class="font-medium capitalize">{intent}</span>
                        <span class="px-3 py-1 bg-brand text-white rounded-full text-sm font-bold">{count}</span>
                    </div>
"""
        
        html += """                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center text-sm text-gray-500 mt-12 pb-8">
            <p>Report generato il {audit['metadata']['timestamp']} · Turismo Torino SEO Audit Tool</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Dashboard HTML salvata in {filepath}")


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
