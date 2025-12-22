# UX Layout Generation Stage Implementation
"""
UX stage that generates HTML/CSS landing pages.
Uses:
- M15: SBA for brand visual constraints
- M18: Drift detection for visual consistency
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class UXOutput:
    """Structured output from UX stage."""

    landing_html: str
    landing_css: str
    component_map: Dict[str, bool]


class UXStage:
    """UX Layout Generation Stage."""

    async def execute(
        self,
        landing_copy: Dict[str, Any],
        brand_visual: Dict[str, Any],
        brand_name: str,
    ) -> UXOutput:
        """Execute UX generation."""
        primary_color = brand_visual.get("primary_color", "#3B82F6")
        secondary_color = brand_visual.get("secondary_color", "#1E40AF")
        font_heading = brand_visual.get("font_heading", "Inter")
        font_body = brand_visual.get("font_body", "Inter")

        hero = landing_copy.get("hero", {})

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{brand_name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="header">
        <nav class="nav">
            <div class="logo">{brand_name}</div>
            <div class="nav-links">
                <a href="#features">Features</a>
                <a href="#pricing">Pricing</a>
                <a href="#contact">Contact</a>
            </div>
            <button class="cta-button">{hero.get('cta', 'Get Started')}</button>
        </nav>
    </header>

    <main>
        <section class="hero">
            <h1>{hero.get('headline', brand_name)}</h1>
            <p class="subhead">{hero.get('subhead', '')}</p>
            <button class="cta-button cta-large">{hero.get('cta', 'Get Started')}</button>
        </section>

        <section id="features" class="features">
            <h2>Features</h2>
            <div class="feature-grid">
                <!-- Features injected here -->
            </div>
        </section>
    </main>

    <footer class="footer">
        <p>&copy; 2025 {brand_name}. All rights reserved.</p>
    </footer>
</body>
</html>"""

        css = f"""/* {brand_name} Landing Page Styles */

:root {{
    --primary-color: {primary_color};
    --secondary-color: {secondary_color};
    --font-heading: '{font_heading}', sans-serif;
    --font-body: '{font_body}', sans-serif;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: var(--font-body);
    line-height: 1.6;
    color: #333;
}}

h1, h2, h3 {{
    font-family: var(--font-heading);
}}

.header {{
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.nav {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
}}

.nav-links a {{
    margin: 0 1rem;
    text-decoration: none;
    color: #666;
}}

.cta-button {{
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
}}

.cta-button:hover {{
    background: var(--secondary-color);
}}

.hero {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 4rem 2rem;
    text-align: center;
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #111;
}}

.subhead {{
    font-size: 1.25rem;
    color: #666;
    margin-bottom: 2rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}}

.cta-large {{
    padding: 1rem 2rem;
    font-size: 1.1rem;
}}

.features {{
    background: #f8fafc;
    padding: 4rem 2rem;
}}

.features h2 {{
    text-align: center;
    margin-bottom: 2rem;
}}

.feature-grid {{
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}}

.footer {{
    background: #1e293b;
    color: white;
    text-align: center;
    padding: 2rem;
}}

@media (max-width: 768px) {{
    .nav {{
        flex-direction: column;
        gap: 1rem;
    }}

    .hero h1 {{
        font-size: 2rem;
    }}
}}
"""

        return UXOutput(
            landing_html=html,
            landing_css=css,
            component_map={
                "header": True,
                "hero": True,
                "features": True,
                "footer": True,
            },
        )
