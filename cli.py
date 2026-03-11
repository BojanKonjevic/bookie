#!/usr/bin/env python3
"""bookie — a clean CLI for the Bookie bookmark API."""

from __future__ import annotations

import os
from uuid import UUID

import httpx
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# ── theme ──────────────────────────────────────────────────────────────────

THEME = Theme(
    {
        "accent": "bold #C084FC",
        "muted": "dim #6B7280",
        "success": "bold #34D399",
        "danger": "bold #F87171",
        "warn": "bold #FBBF24",
        "url": "#60A5FA underline",
        "tag": "bold #F9A8D4",
        "id": "dim #9CA3AF",
        "title": "bold white",
    }
)

console = Console(theme=THEME, highlight=False)
err_console = Console(theme=THEME, stderr=True)

# ── app ────────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="bookie",
    help="Manage your bookmarks from the terminal.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)
bookmarks_app = typer.Typer(help="Bookmark operations.", no_args_is_help=True)
tags_app = typer.Typer(help="Tag operations.", no_args_is_help=True)
app.add_typer(bookmarks_app, name="bookmarks", rich_help_panel="Commands")
app.add_typer(tags_app, name="tags", rich_help_panel="Commands")


# ── helpers ────────────────────────────────────────────────────────────────


def get_base_url(ctx: typer.Context) -> str:
    return ctx.obj.get("base_url", "http://localhost:8000")


def client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=10)


def abort(msg: str) -> None:
    err_console.print(f"[danger]✗[/danger] {msg}")
    raise typer.Exit(1)


def handle_response(r: httpx.Response) -> dict | list:
    if r.status_code == 204:
        return {}
    if r.is_success:
        return r.json()
    try:
        detail = r.json().get("detail", r.text)
    except Exception:
        detail = r.text
    abort(f"[{r.status_code}] {detail}")
    return {}  # unreachable


def fmt_tags(tags: list[dict]) -> Text:
    if not tags:
        return Text("—", style="muted")
    t = Text()
    for i, tag in enumerate(tags):
        if i:
            t.append("  ", style="")
        t.append(f"#{tag['name']}", style="tag")
    return t


def fmt_bool(val: bool) -> Text:
    return Text("★", style="warn") if val else Text("☆", style="muted")


def fmt_id(val: str) -> Text:
    short = val[:8] + "…"
    return Text(short, style="id")


def render_bookmark_table(items: list[dict], title: str = "Bookmarks") -> None:
    if not items:
        console.print(
            Panel(
                "[muted]No bookmarks found.[/muted]", title=title, border_style="accent"
            )
        )
        return

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="accent",
        header_style="accent",
        show_lines=True,
        expand=False,
        title_style="bold white",
    )
    table.add_column("", width=2, justify="center")  # fav
    table.add_column("ID", style="id", no_wrap=True)
    table.add_column("Title", style="title", min_width=20, max_width=40)
    table.add_column("URL", style="url", max_width=45, overflow="fold")
    table.add_column("Tags")
    table.add_column("Created", style="muted", no_wrap=True)

    for b in items:
        created = b["created_at"][:10]
        table.add_row(
            fmt_bool(b["favorite"]),
            fmt_id(b["id"]),
            b["title"],
            b["url"],
            fmt_tags(b["tags"]),
            created,
        )

    console.print()
    console.print(table)
    console.print(f"  [muted]{len(items)} result(s)[/muted]")
    console.print()


def render_bookmark_detail(b: dict) -> None:
    created = b["created_at"].replace("T", " ")[:19]
    fav_line = (
        "[warn]★ Favorited[/warn]"
        if b["favorite"]
        else "[muted]☆ Not favorited[/muted]"
    )

    body = Text()
    body.append(f"  {b['title']}\n", style="bold white")
    body.append(f"  {b['url']}\n", style="url")
    body.append(f"\n  {fav_line}\n", style="")

    if b.get("description"):
        body.append(f"\n  {b['description']}\n", style="white")

    body.append("\n  Tags: ", style="muted")
    body.append_text(fmt_tags(b["tags"]))
    body.append(f"\n  Created: {created}", style="muted")
    body.append(f"\n  ID: {b['id']}", style="id")

    console.print()
    console.print(Panel(body, border_style="accent", padding=(0, 1)))
    console.print()


# ── global options ─────────────────────────────────────────────────────────


@app.callback()
def main(
    ctx: typer.Context,
    base_url: str = typer.Option(
        None,
        "--base-url",
        "-H",
        envvar="BOOKIE_URL",
        help="API base URL. Defaults to [accent]http://localhost:8000[/accent].",
        show_default=False,
    ),
) -> None:
    """
    [accent]bookie[/accent] — a clean CLI for the Bookie bookmark API.

    Set [accent]BOOKIE_URL[/accent] to avoid passing [accent]--base-url[/accent].
    """
    ctx.ensure_object(dict)
    ctx.obj["base_url"] = base_url or os.environ.get(
        "BOOKIE_URL", "http://localhost:8000"
    )


# ── bookmarks ──────────────────────────────────────────────────────────────


@bookmarks_app.command("list")
def bookmarks_list(
    ctx: typer.Context,
    favorite: bool | None = typer.Option(
        None, "--favorite/--all", "-f/-a", help="Filter by favorite status."
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-t", help="Filter by tag name (repeatable)."
    ),
    search: str | None = typer.Option(
        None, "--search", "-s", help="Full-text search term."
    ),
    page: int = typer.Option(1, "--page", "-p", help="Page number."),
    limit: int = typer.Option(10, "--limit", "-l", help="Results per page."),
) -> None:
    """List bookmarks with optional filters."""
    params: dict = {"page": page, "limit": limit}
    if favorite is not None:
        params["favorite"] = favorite
    if tags:
        params["tags"] = tags
    if search:
        params["search"] = search

    with client(get_base_url(ctx)) as c:
        r = c.get("/bookmarks", params=params)

    items = handle_response(r)
    assert isinstance(items, list)

    title_parts = ["Bookmarks"]
    if search:
        title_parts.append(f'search="{search}"')
    if tags:
        title_parts.append("tags=" + ",".join(tags))
    if favorite is not None:
        title_parts.append("favorites" if favorite else "non-favorites")
    title_parts.append(f"page {page}")

    render_bookmark_table(items, title="  ".join(title_parts))


@bookmarks_app.command("get")
def bookmarks_get(
    ctx: typer.Context,
    bookmark_id: UUID = typer.Argument(..., help="Bookmark UUID."),
) -> None:
    """Get a single bookmark by ID."""
    with client(get_base_url(ctx)) as c:
        r = c.get(f"/bookmarks/{bookmark_id}")

    b = handle_response(r)
    assert isinstance(b, dict)
    render_bookmark_detail(b)


@bookmarks_app.command("create")
def bookmarks_create(
    ctx: typer.Context,
    title: str = typer.Option(
        ..., "--title", "-T", help="Bookmark title.", prompt="Title"
    ),
    url: str = typer.Option(..., "--url", "-u", help="Bookmark URL.", prompt="URL"),
    description: str | None = typer.Option(
        None, "--description", "-d", help="Optional description."
    ),
    favorite: bool = typer.Option(
        False, "--favorite", "-f", is_flag=True, help="Mark as favorite."
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-t", help="Tag names (repeatable)."
    ),
) -> None:
    """Create a new bookmark."""
    payload: dict = {
        "title": title,
        "url": url,
        "favorite": favorite,
        "tags": tags or [],
    }
    if description:
        payload["description"] = description

    with client(get_base_url(ctx)) as c:
        r = c.post("/bookmarks", json=payload)

    b = handle_response(r)
    assert isinstance(b, dict)
    console.print("\n[success]✓[/success] Bookmark created")
    render_bookmark_detail(b)


@bookmarks_app.command("update")
def bookmarks_update(
    ctx: typer.Context,
    bookmark_id: UUID = typer.Argument(..., help="Bookmark UUID."),
    title: str | None = typer.Option(None, "--title", "-T", help="New title."),
    url: str | None = typer.Option(None, "--url", "-u", help="New URL."),
    description: str | None = typer.Option(
        None, "--description", "-d", help="New description."
    ),
    favorite: bool | None = typer.Option(
        None, "--favorite/--no-favorite", "-f/-F", help="Favorite status."
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-t", help="Replace tags (repeatable)."
    ),
) -> None:
    """Update an existing bookmark (only supplied fields are changed)."""
    payload: dict = {}
    if title is not None:
        payload["title"] = title
    if url is not None:
        payload["url"] = url
    if description is not None:
        payload["description"] = description
    if favorite is not None:
        payload["favorite"] = favorite
    if tags is not None:
        payload["tags"] = tags

    if not payload:
        abort("No fields to update — pass at least one option.")

    with client(get_base_url(ctx)) as c:
        r = c.patch(f"/bookmarks/{bookmark_id}", json=payload)

    b = handle_response(r)
    assert isinstance(b, dict)
    console.print("\n[success]✓[/success] Bookmark updated")
    render_bookmark_detail(b)


@bookmarks_app.command("delete")
def bookmarks_delete(
    ctx: typer.Context,
    bookmark_id: UUID = typer.Argument(..., help="Bookmark UUID."),
    yes: bool = typer.Option(
        False, "--yes", "-y", is_flag=True, help="Skip confirmation prompt."
    ),
) -> None:
    """Delete a bookmark by ID."""
    if not yes:
        typer.confirm(f"Delete bookmark {str(bookmark_id)[:8]}…?", abort=True)

    with client(get_base_url(ctx)) as c:
        r = c.delete(f"/bookmarks/{bookmark_id}")

    handle_response(r)
    console.print(
        f"\n[success]✓[/success] Bookmark [id]{str(bookmark_id)[:8]}…[/id] deleted.\n"
    )


# ── tags ───────────────────────────────────────────────────────────────────


@tags_app.command("list")
def tags_list(ctx: typer.Context) -> None:
    """List all tags."""
    with client(get_base_url(ctx)) as c:
        r = c.get("/tags")

    items = handle_response(r)
    assert isinstance(items, list)

    if not items:
        console.print(
            Panel("[muted]No tags found.[/muted]", title="Tags", border_style="accent")
        )
        return

    table = Table(
        title="Tags",
        box=box.ROUNDED,
        border_style="accent",
        header_style="accent",
        title_style="bold white",
    )
    table.add_column("ID", style="id")
    table.add_column("Name", style="tag")

    for tag in items:
        table.add_row(tag["id"], f"#{tag['name']}")

    console.print()
    console.print(table)
    console.print(f"  [muted]{len(items)} tag(s)[/muted]\n")


@tags_app.command("get")
def tags_get(
    ctx: typer.Context,
    tag_id: UUID = typer.Argument(..., help="Tag UUID."),
) -> None:
    """Get a single tag by ID."""
    with client(get_base_url(ctx)) as c:
        r = c.get(f"/tags/{tag_id}")

    tag = handle_response(r)
    assert isinstance(tag, dict)

    console.print()
    console.print(
        Panel(
            f"  [tag]#{tag['name']}[/tag]\n  [id]{tag['id']}[/id]",
            title="Tag",
            border_style="accent",
            padding=(0, 1),
        )
    )
    console.print()


# ── ping ───────────────────────────────────────────────────────────────────


@app.command()
def ping(ctx: typer.Context) -> None:
    """Check that the API is reachable."""
    base_url = get_base_url(ctx)
    try:
        with client(base_url) as c:
            r = c.get("/")
        if r.is_success:
            console.print(
                f"\n[success]✓[/success] API is up at [accent]{base_url}[/accent]\n"
            )
        else:
            abort(f"API returned {r.status_code}")
    except httpx.ConnectError:
        abort(f"Could not reach {base_url}")


if __name__ == "__main__":
    app()
