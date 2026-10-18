"""Resource ownership for standalone applications and mounted integration."""
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    try:
        await app.state.resources.start()
        yield
    finally:
        await app.state.resources.close()


def mounted_style_lifespan(parent_lifespan, style_app):
    @asynccontextmanager
    async def combined(parent_app):
        async with parent_lifespan(parent_app):
            async with style_app.router.lifespan_context(style_app):
                yield
    return combined
