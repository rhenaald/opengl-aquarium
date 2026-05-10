"""Fish shape and geometry utilities library."""

from .shape import (
    # Vector utilities
    norm,
    cross,
    face_normal,
    lerp3,
    # Vertex building
    add_tri,
    add_quad,
    add_tri_auto,
    add_quad_auto,
    add_ds_tri,
    add_ds_quad,
    # Body profile
    body_x,
    body_radius,
    body_point,
    body_normal,
    # Mesh builders
    build_body,
    build_mouth,
    build_eyes,
    build_gills,
    build_caudal,
    build_dorsal,
    build_anal,
    build_pectorals,
    build_pelvics,
    build_lateral_line,
)

__all__ = [
    'norm',
    'cross',
    'face_normal',
    'lerp3',
    'add_tri',
    'add_quad',
    'add_tri_auto',
    'add_quad_auto',
    'add_ds_tri',
    'add_ds_quad',
    'body_x',
    'body_radius',
    'body_point',
    'body_normal',
    'build_body',
    'build_mouth',
    'build_eyes',
    'build_gills',
    'build_caudal',
    'build_dorsal',
    'build_anal',
    'build_pectorals',
    'build_pelvics',
    'build_lateral_line',
]
