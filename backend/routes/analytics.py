"""
Analytics dashboard routes.
"""

from flask import Blueprint, render_template


analytics_bp = Blueprint(
    "analytics",
    __name__,
)


@analytics_bp.route("/analytics")
def analytics():
    return render_template("analytics.html")