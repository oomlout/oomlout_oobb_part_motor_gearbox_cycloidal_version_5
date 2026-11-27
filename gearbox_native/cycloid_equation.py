"""Independent analytic reference and metadata for the cycloid.

t is in radians, N is the ring contact count, R is the pitch radius, e is the
eccentricity, and a = roller_radius + clearance. There are N-1 disc lobes.

u = R cos(t) - N e cos(N t)
v = R sin(t) - N e sin(N t)
s = sqrt(u*u + v*v)
x = R cos(t) - e cos(N t) - a*u/s
y = R sin(t) - e sin(N t) - a*v/s

The active native recipe uses the helper's cycloidal_disc / parametric_profile
implementation. This separate evaluator supports diagnostics and legacy recipes.
"""
from dataclasses import dataclass
from math import cos, sin, hypot


@dataclass(frozen=True)
class CycloidEquation:
    contacts: int
    pitch_radius: float
    eccentricity: float
    roller_radius: float
    clearance: float = 0.0

    def minimum_convex_radius(self):
        """Smallest inward-offset radius before the roller-centre curve cusps.

        Signed curvature is (C-D*cos((N-1)t))/(A-B*cos((N-1)t))**1.5.
        Its maximum occurs at an endpoint or the one stationary cosine below.
        """
        n,r,e=self.contacts,self.pitch_radius,self.eccentricity
        if r<=n*e or e<=0:
            raise ValueError('Cycloid requires 0 < N*eccentricity < pitch radius')
        a=r*r+n*n*e*e;b=2*n*r*e
        c=r*r+n**3*e*e;d=n*(n+1)*r*e
        stationary=max(-1.,min(1.,(3*b*c-2*d*a)/(b*d)))
        curvature=max((c-d*u)/(a-b*u)**1.5 for u in (-1.,1.,stationary))
        return 1/curvature

    def validate_offset(self):
        if self.roller_radius+self.clearance>=self.minimum_convex_radius():
            raise ValueError('Lobe radius and clearance undercut the cycloid; increase pitch radius or reduce eccentricity')

    def point(self,t):
        n,r,e=self.contacts,self.pitch_radius,self.eccentricity
        u=r*cos(t)-n*e*cos(n*t);v=r*sin(t)-n*e*sin(n*t)
        speed=hypot(u,v)
        if speed<=0:raise ValueError('Cycloid equation is singular; reduce eccentricity')
        offset=self.roller_radius+self.clearance
        return [r*cos(t)-e*cos(n*t)-offset*u/speed,
                r*sin(t)-e*sin(n*t)-offset*v/speed]

    def definition(self):
        return dict(name='cycloidal_roller_envelope',parameter='t',domain=[0,'2*pi'],angle_unit='radians',
            parameters=dict(N=self.contacts,R=self.pitch_radius,e=self.eccentricity,
                            roller_radius=self.roller_radius,clearance=self.clearance),
            expressions=dict(a='roller_radius + clearance',u='R*cos(t) - N*e*cos(N*t)',
                v='R*sin(t) - N*e*sin(N*t)',s='sqrt(u*u + v*v)',
                x='R*cos(t) - e*cos(N*t) - a*u/s',y='R*sin(t) - e*sin(N*t) - a*v/s'),
            native_representation='adaptive polygon generated from equation; installed API has no equation curve')
