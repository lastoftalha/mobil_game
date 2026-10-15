from django.db.models import F
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.core.utils import plain

from .models import Post


def post_detail(request, slug):
    qs = Post.objects.select_related("category")
    if not (request.user.is_authenticated and request.user.is_staff):
        qs = qs.published()
    post = get_object_or_404(qs, slug=slug)

    session_key = f"viewed_post_{post.pk}"
    if not request.session.get(session_key):
        Post.objects.filter(pk=post.pk).update(views=F("views") + 1)
        request.session[session_key] = True
        post.views += 1

    related = Post.objects.published().exclude(pk=post.pk)
    if post.category_id:
        same = list(related.filter(category_id=post.category_id)[:3])
        if len(same) < 3:
            same += list(related.exclude(pk__in=[p.pk for p in same])[: 3 - len(same)])
        related = same
    else:
        related = list(related[:3])

    context = {
        "post": post,
        "related_posts": related,
        "meta_title": plain(post.meta_title or post.title),
        "meta_description": post.meta_description or post.summary,
        "meta_image": post.cover.url if post.cover else "",
        "meta_type": "article",
        "body_class": "page-post",
        "panel_edit_url": reverse("panel:edit", args=["blog", post.pk]),
    }
    return render(request, "site/post_detail.html", context)
