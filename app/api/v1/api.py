from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, courses, syllabus, materials, recommendations, tutor, dashboard, admin, course_materials, analytics, lecturer_materials

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(course_materials.router, prefix="/courses", tags=["course-materials"])
api_router.include_router(syllabus.router, prefix="/syllabus", tags=["syllabus"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(lecturer_materials.router, prefix="/lecturer/materials", tags=["Lecturer Materials"])
