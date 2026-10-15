"""Bölüm tiplerine göre şablona gönderilecek verileri hazırlar."""
from django.core.paginator import Paginator
from django.db.models import Q


def _limit(section, default):
    return section.limit or default


def _brands_marquee(section, ctx):
    from apps.content.models import Brand

    qs = Brand.objects.filter(is_active=True, show_in_marquee=True)
    return {"brands": list(qs[: _limit(section, 40)])}


def _hero_home(section, ctx):
    return {"slides": [i for i in section.active_items() if i.image]}


def _page_hero(section, ctx):
    items = section.active_items()
    links = [{"title": i.title, "note": i.subtitle, "url": i.url} for i in items if i.title]
    if not links and not section.image and section.page.system_key == "services":
        from apps.content.models import Service

        links = [{"title": s.title, "note": "", "url": s.get_absolute_url()}
                 for s in Service.objects.filter(is_active=True).only("title", "slug")]
    return {"hero_links": links}


def _featured_work(section, ctx):
    from apps.content.models import Project

    qs = Project.objects.filter(is_active=True, is_featured=True).select_related("category")
    return {"projects": list(qs[: _limit(section, 4)])}


def _capabilities(section, ctx):
    items = section.active_items()
    if items:
        words = [{"title": i.title, "text": i.text, "url": i.url} for i in items]
    else:
        from apps.content.models import Service

        words = [
            {"title": s.title, "text": s.short_description, "url": s.get_absolute_url()}
            for s in Service.objects.filter(is_active=True, show_on_home=True)
        ]
    return {"words": words}


def _services_list(section, ctx):
    from apps.content.models import Service

    qs = Service.objects.filter(is_active=True)
    if section.limit:
        qs = qs[: section.limit]
    return {"services": list(qs)}


def _portfolio_grid(section, ctx):
    from apps.content.models import Project, ProjectCategory

    qs = Project.objects.filter(is_active=True).select_related("category")
    if section.limit:
        qs = qs[: section.limit]
    projects = list(qs)
    used = {p.category_id for p in projects if p.category_id}
    categories = [c for c in ProjectCategory.objects.all() if c.pk in used]
    return {"projects": projects, "categories": categories}


def _gallery_grid(section, ctx):
    from apps.content.models import GalleryCategory, GalleryImage

    qs = GalleryImage.objects.filter(is_active=True).select_related("category")
    if section.limit:
        qs = qs[: section.limit]
    images = list(qs)
    used = {i.category_id for i in images if i.category_id}
    categories = [c for c in GalleryCategory.objects.all() if c.pk in used]
    return {"images": images, "categories": categories}


def _brands_grid(section, ctx):
    from apps.content.models import Brand

    qs = Brand.objects.filter(is_active=True, show_in_references=True)
    if section.limit:
        qs = qs[: section.limit]
    return {"brands": list(qs)}


def _testimonials(section, ctx):
    from apps.content.models import Testimonial

    return {"testimonials": list(Testimonial.objects.filter(is_active=True)[: _limit(section, 20)])}


def _faq(section, ctx):
    items = section.active_items()
    if items:
        faqs = [{"question": i.title, "answer": i.text} for i in items]
    else:
        from apps.content.models import FAQ

        qs = FAQ.objects.filter(is_active=True, service__isnull=True)
        faqs = [{"question": f.question, "answer": f.answer} for f in qs[: _limit(section, 20)]]
    return {"faqs": faqs}


def _blog_latest(section, ctx):
    from apps.blog.models import Post

    qs = Post.objects.published().select_related("category")
    return {"posts": list(qs[: _limit(section, 3)])}


def _blog_list(section, ctx):
    from apps.blog.models import Category, Post

    request = ctx.get("request")
    params = request.GET if request is not None else {}
    qs = Post.objects.published().select_related("category")
    active_cat = None
    cat_slug = params.get("kategori", "")
    if cat_slug:
        active_cat = Category.objects.filter(slug=cat_slug).first()
        if active_cat:
            qs = qs.filter(category=active_cat)
    query = (params.get("q") or "").strip()[:100]
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(tags__icontains=query))
    paginator = Paginator(qs, _limit(section, 9))
    page_obj = paginator.get_page(params.get("sayfa"))
    used = set(Post.objects.published().exclude(category=None).values_list("category_id", flat=True))
    categories = [c for c in Category.objects.all() if c.pk in used]
    return {
        "page_obj": page_obj,
        "posts": list(page_obj.object_list),
        "categories": categories,
        "active_category": active_cat,
        "query": query,
    }


def _contact_form(section, ctx):
    from apps.contact.forms import ContactForm
    from apps.content.models import Service

    form = ctx.get("contact_form") or ContactForm(services=Service.objects.filter(is_active=True))
    return {"form": form}


PROVIDERS = {
    "hero_home": _hero_home,
    "page_hero": _page_hero,
    "logo_marquee": _brands_marquee,
    "featured_work": _featured_work,
    "capabilities": _capabilities,
    "services_list": _services_list,
    "portfolio_grid": _portfolio_grid,
    "gallery_grid": _gallery_grid,
    "brands_grid": _brands_grid,
    "testimonials": _testimonials,
    "faq": _faq,
    "blog_latest": _blog_latest,
    "blog_list": _blog_list,
    "contact_form": _contact_form,
}


def build_section_context(section, ctx):
    data = {"section": section, "items": section.active_items(), "theme": section.resolved_theme}
    provider = PROVIDERS.get(section.type)
    if provider:
        data.update(provider(section, ctx))
    return data
