class TemplateRenderService:
    def render(self, context: dict) -> str:
        banner = '<div style="background:#f59e0b;color:#111827;padding:12px;text-align:center;font-weight:700">Temporary draft/demo site</div>' if context.get('is_demo') else ''
        return f"""<!doctype html>
<html lang='en'>
  <head>
    <meta charset='utf-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <meta name='robots' content='noindex,nofollow' />
    <title>{context['site_title']}</title>
    <style>
      body {{ font-family: Arial, sans-serif; background:#f8fafc; color:#111827; margin:0; }}
      main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px; }}
      .card {{ background:#fff; border-radius:18px; padding:24px; box-shadow:0 10px 24px rgba(0,0,0,.06); }}
      .cta {{ display:inline-block; background:#111827; color:#fff; padding:12px 16px; border-radius:12px; text-decoration:none; margin-top:16px; }}
    </style>
  </head>
  <body>
    {banner}
    <main>
      <div class='card'>
        <h1>{context['hero_title']}</h1>
        <p>{context['about_text']}</p>
        <a class='cta' href='#contact'>Contact</a>
      </div>
      <div id='contact' class='card' style='margin-top:16px'>
        <h2>Contact</h2>
        <p>This page is ready for outreach preview and basic activation workflows.</p>
      </div>
    </main>
  </body>
</html>"""
