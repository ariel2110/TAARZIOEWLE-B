from __future__ import annotations

import html
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.demo_site import DemoSite
from app.models.draft_site import DraftSite
from app.services.public.site_domain_service import parse_subdomain_from_host, build_draft_subdomain, normalize_dns_label

router = APIRouter(prefix='/public', tags=['public-sites'])


def _render_demo_html(demo: DemoSite) -> str:
    """Render a demo site using the TAZO template system."""
    try:
        from app.services.generator.template_render_service import TemplateRenderService
        ctx = {
            'site_title': demo.business_name,
            'hero_title': demo.business_name,
            'phone': demo.phone,
            'city': demo.city,
            'address': demo.address,
            'category': demo.category or '',
            'business_types': demo.business_types or '',
            'about_text': demo.top_review,
            'tagline': demo.tagline,
            'rating': demo.rating,
            'reviews_count': demo.reviews_count,
            'maps_url': demo.google_maps_url,
          'opening_hours': demo.opening_hours,
          'reviews_json': demo.reviews_json,
          'photo_url': demo.photo_url,
          'website': demo.website,
            'is_demo': True,
        }
        return TemplateRenderService().render(ctx)
    except Exception:
        pass  # Fall back to basic template on error
    rating = f"{demo.rating:.1f}" if demo.rating is not None else '4.8'
    reviews_count = demo.reviews_count or 0
    top_review = html.escape(demo.top_review or 'שירות מקצועי, אדיב ומהיר. מומלץ בחום!')
    business_name = html.escape(demo.business_name)
    tagline = html.escape(demo.tagline or 'שירות מקצועי, אמין ומהיר')
    city = html.escape(demo.city or '')
    phone = html.escape(demo.phone or '')
    address = html.escape(demo.address or '')
    maps = html.escape(demo.google_maps_url or '#')

    return f"""<!DOCTYPE html>
<html lang=\"he\" dir=\"rtl\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{business_name} | tazo-web Demo</title>
  <script src=\"https://cdn.tailwindcss.com\"></script>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700;800&display=swap\" rel=\"stylesheet\">
  <style>body {{ font-family: Heebo, sans-serif; }}</style>
</head>
<body class=\"bg-slate-950 text-white\">
  <section class=\"min-h-screen bg-gradient-to-b from-slate-900 to-slate-950\">
    <div class=\"max-w-5xl mx-auto px-6 py-14\">
      <div class=\"inline-flex bg-amber-400 text-slate-900 px-3 py-1 rounded-full text-sm font-bold\">tazo-web Demo</div>
      <h1 class=\"text-4xl md:text-6xl font-extrabold mt-5 leading-tight\">{business_name}</h1>
      <p class=\"text-xl text-slate-300 mt-4\">{tagline}</p>
      <div class=\"mt-8 flex flex-wrap gap-3\">
        <span class=\"bg-white/10 rounded-full px-4 py-2\">⭐ {rating} ({reviews_count} ביקורות)</span>
        {f'<span class="bg-white/10 rounded-full px-4 py-2">📍 {city}</span>' if city else ''}
        {f'<span class="bg-white/10 rounded-full px-4 py-2">📞 {phone}</span>' if phone else ''}
      </div>
      <div class=\"mt-8 bg-white text-slate-900 rounded-2xl p-6 shadow-2xl\">
        <div class=\"text-xl font-bold mb-2\">מה לקוחות אומרים</div>
        <p class=\"leading-8\">\"{top_review}\"</p>
      </div>
      <div class=\"mt-10 flex flex-wrap gap-3\">
        {f'<a href="tel:{phone}" class="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-5 py-3 rounded-xl font-bold">חייגו עכשיו</a>' if phone else ''}
        <a href=\"{maps}\" target=\"_blank\" rel=\"noopener noreferrer\" class=\"bg-amber-400 hover:bg-amber-300 text-slate-900 px-5 py-3 rounded-xl font-bold\">ניווט בגוגל מפות</a>
      </div>
      {f'<p class="text-slate-400 mt-8">{address}</p>' if address else ''}
    </div>
  </section>
</body>
</html>"""


def _draft_html_path(draft: DraftSite) -> Path:
  if draft.preview_url:
    rel = draft.preview_url.lstrip('/')
    if rel.startswith('static/'):
      rel = f"static_sites/{rel[len('static/'):]}"
    return Path(__file__).resolve().parents[3] / rel
  return Path(__file__).resolve().parents[3] / 'static_sites' / 'drafts' / f'draft_{draft.id}.html'


@router.get('/site-by-host', response_class=HTMLResponse)
def site_by_host(request: Request, db: Session = Depends(get_db)):
    sub = parse_subdomain_from_host(request.headers.get('host', ''))
    if not sub:
        raise HTTPException(status_code=404, detail='Site not found')

    # 1) Demo subdomain lookup by exact slug
    demo = db.query(DemoSite).filter(DemoSite.slug == sub).first()
    if not demo:
      for item in db.query(DemoSite).all():
        if normalize_dns_label(item.slug) == sub:
          demo = item
          break
    if demo:
        return HTMLResponse(_render_demo_html(demo))

    # 2) Draft site lookup by id suffix in subdomain label, e.g. my-biz-19
    m = re.search(r'-(\d+)$', sub)
    if not m:
        raise HTTPException(status_code=404, detail='Site not found')

    draft_id = int(m.group(1))
    draft = db.query(DraftSite).filter(DraftSite.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail='Site not found')

    business_name = getattr(draft.business, 'name', '') if getattr(draft, 'business', None) else ''
    expected = build_draft_subdomain(draft.id, business_name)
    if sub != expected and not sub.endswith(f'-{draft.id}'):
        raise HTTPException(status_code=404, detail='Site not found')

    html_path = _draft_html_path(draft)
    if not html_path.exists():
        # Best effort regeneration if file missing.
        from app.services.draft_sites.draft_site_service import DraftSiteService
        DraftSiteService().generate_preview(db, draft.id)

    if not html_path.exists():
        raise HTTPException(status_code=404, detail='Site file not found')

    return HTMLResponse(html_path.read_text(encoding='utf-8'))
