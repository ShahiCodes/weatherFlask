import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db

class FavouriteCities(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key = True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), unique = True, nullable = False, index = True)
    
    def __repr__(self):
        return f"<favCity: {self.name}>"