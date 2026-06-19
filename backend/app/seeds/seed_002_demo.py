"""Seed script for demo data: carreras, cohortes, materias, asignaciones, grilla, evaluaciones.

Creates a fully populated TUPAD tenant ready for frontend demonstration.
Idempotent — safe to run multiple times.

Usage:
    python -m app.seeds.seed_002_demo

Requires:
    - seed_001 already run (tenant TUPAD + admin user + roles exist)
    - alembic upgrade head (all tables created, including fechas_evaluacion)
"""

import asyncio
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session_maker
from app.models.asignacion import Asignacion
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.fecha_evaluacion import FechaEvaluacion
from app.models.grilla_salarial import GrupoMateria, SalarioBase, SalarioPlus
from app.models.materia import Materia
from app.models.tenant import Tenant
from app.models.usuario import Usuario

TUPAD_NOMBRE = "TUPAD"
ADMIN_EMAIL = "admin@tupad.edu.ar"


async def seed_demo_data(session: AsyncSession) -> None:
    """Insert demo academic structure, assignments, grilla, and evaluation dates.

    All data is scoped to the TUPAD tenant. The admin user is assigned
    as COORDINADOR to all materias so the frontend shows data immediately.
    """
    # ── Tenant ───────────────────────────────────────────────────────
    result = await session.execute(
        select(Tenant).where(Tenant.nombre == TUPAD_NOMBRE)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        print("ERROR: TUPAD tenant not found. Run seed_001 first.")
        return
    tid = tenant.id
    print(f"Tenant: {TUPAD_NOMBRE} (id={tid})")

    # ── Admin user ───────────────────────────────────────────────────
    from app.models.usuario import Usuario
    uh = Usuario.compute_email_hash(ADMIN_EMAIL)
    result = await session.execute(
        select(Usuario).where(Usuario.tenant_id == tid, Usuario.email_hash == uh)
    )
    admin = result.scalar_one_or_none()
    if admin is None:
        print("ERROR: Admin user not found. Run seed_001 first.")
        return
    uid = admin.id
    print(f"Admin: {ADMIN_EMAIL} (id={uid})")

    # ── Carreras ─────────────────────────────────────────────────────
    carreras_data = [
        {"codigo": "TUPAD", "nombre": "Tecnicatura Universitaria en Programacion y Analisis de Datos"},
        {"codigo": "TUGAP", "nombre": "Tecnicatura Universitaria en Gestion y Analisis de Proyectos"},
    ]
    carreras: dict[str, Carrera] = {}
    for cd in carreras_data:
        result = await session.execute(
            select(Carrera).where(Carrera.tenant_id == tid, Carrera.codigo == cd["codigo"])
        )
        c = result.scalar_one_or_none()
        if c is None:
            c = Carrera(tenant_id=tid, **cd)
            session.add(c)
            await session.flush()
            print(f"  Created carrera: {cd['codigo']}")
        carreras[cd["codigo"]] = c

    # ── Cohortes ─────────────────────────────────────────────────────
    cohortes_data = [
        {"nombre": "MAR-2025", "carrera_codigo": "TUPAD", "anio": 2025, "vig_desde": date(2025, 3, 1)},
        {"nombre": "AGO-2025", "carrera_codigo": "TUPAD", "anio": 2025, "vig_desde": date(2025, 8, 1)},
        {"nombre": "MAR-2026", "carrera_codigo": "TUPAD", "anio": 2026, "vig_desde": date(2026, 3, 1)},
        {"nombre": "MAR-2025", "carrera_codigo": "TUGAP", "anio": 2025, "vig_desde": date(2025, 3, 1)},
    ]
    cohortes: dict[str, Cohorte] = {}
    for cd in cohortes_data:
        car = carreras[cd.pop("carrera_codigo")]
        cd["carrera_id"] = car.id
        cd["tenant_id"] = tid
        result = await session.execute(
            select(Cohorte).where(
                Cohorte.tenant_id == tid,
                Cohorte.carrera_id == car.id,
                Cohorte.nombre == cd["nombre"],
            )
        )
        c = result.scalar_one_or_none()
        if c is None:
            c = Cohorte(**cd)
            session.add(c)
            await session.flush()
            print(f"  Created cohorte: {cd['nombre']} ({car.codigo})")
        cohortes[f"{car.codigo}/{cd['nombre']}"] = c

    # ── Materias ─────────────────────────────────────────────────────
    materias_data = [
        {"codigo": "PROG1", "nombre": "Programacion I"},
        {"codigo": "PROG2", "nombre": "Programacion II"},
        {"codigo": "BD1",   "nombre": "Base de Datos I"},
        {"codigo": "BD2",   "nombre": "Base de Datos II"},
        {"codigo": "MAT1",  "nombre": "Matematica I"},
        {"codigo": "ING1",  "nombre": "Ingles I"},
        {"codigo": "ARQ1",  "nombre": "Arquitectura de Computadoras"},
        {"codigo": "PROY1", "nombre": "Gestion de Proyectos"},
    ]
    materias: dict[str, Materia] = {}
    for md in materias_data:
        md["tenant_id"] = tid
        result = await session.execute(
            select(Materia).where(Materia.tenant_id == tid, Materia.codigo == md["codigo"])
        )
        m = result.scalar_one_or_none()
        if m is None:
            m = Materia(**md)
            session.add(m)
            await session.flush()
            print(f"  Created materia: {md['codigo']} - {md['nombre']}")
        materias[md["codigo"]] = m

    # ── Asignaciones — admin as COORDINADOR for all materias ────────
    tupad_cohortes = [
        cohortes["TUPAD/MAR-2025"],
        cohortes["TUPAD/AGO-2025"],
        cohortes["TUPAD/MAR-2026"],
    ]
    tupad_carrera = carreras["TUPAD"]
    comisiones_opts = [["A", "B"], ["A"], ["B", "C"]]

    asignaciones_created = 0
    for i, mat in enumerate(materias.values()):
        for j, coh in enumerate(tupad_cohortes):
            com = comisiones_opts[(i + j) % 3]
            result = await session.execute(
                select(Asignacion).where(
                    Asignacion.tenant_id == tid,
                    Asignacion.usuario_id == uid,
                    Asignacion.materia_id == mat.id,
                    Asignacion.cohorte_id == coh.id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                a = Asignacion(
                    tenant_id=tid,
                    usuario_id=uid,
                    rol="COORDINADOR",
                    materia_id=mat.id,
                    carrera_id=tupad_carrera.id,
                    cohorte_id=coh.id,
                    comisiones=com,
                    vig_desde=date(2025, 3, 1),
                )
                session.add(a)
                asignaciones_created += 1

    if asignaciones_created > 0:
        await session.flush()
        print(f"  Created {asignaciones_created} asignaciones for admin")

    # ── Grilla Salarial (demo data for liquidaciones) ────────────────
    roles_salario = ["PROFESOR", "TUTOR", "COORDINADOR", "NEXO"]
    for rol in roles_salario:
        result = await session.execute(
            select(SalarioBase).where(
                SalarioBase.tenant_id == tid,
                SalarioBase.rol == rol,
            )
        )
        sb = result.scalar_one_or_none()
        if sb is None:
            sb = SalarioBase(
                tenant_id=tid,
                rol=rol,
                monto=150000.00 if rol != "NEXO" else 50000.00,
                desde=date(2025, 1, 1),
            )
            session.add(sb)
            print(f"  Created SalarioBase: {rol}")

    # Grupos de materia para plus salarial
    result = await session.execute(
        select(GrupoMateria).where(GrupoMateria.tenant_id == tid, GrupoMateria.grupo == "BASICAS")
    )
    gm = result.scalar_one_or_none()
    if gm is None:
        gm = GrupoMateria(tenant_id=tid, grupo="BASICAS", descripcion="Matematica, Arquitectura")
        session.add(gm)
        await session.flush()

        # SalarioPlus for this group
        for rol in ["PROFESOR", "TUTOR"]:
            result = await session.execute(
                select(SalarioPlus).where(
                    SalarioPlus.tenant_id == tid,
                    SalarioPlus.grupo == gm.grupo,
                    SalarioPlus.rol == rol,
                )
            )
            sp = result.scalar_one_or_none()
            if sp is None:
                sp = SalarioPlus(
                    tenant_id=tid,
                    grupo=gm.grupo,
                    rol=rol,
                    monto=20000.00,
                    descripcion="Plus por grupo de Ciencias Basicas",
                    desde=date(2025, 1, 1),
                )
                session.add(sp)
        print(f"  Created GrupoMateria + SalarioPlus: {gm.grupo}")

    # ── Fechas de Evaluacion (demo for calendario) ──────────────────
    if materias and tupad_cohortes:
        fechas_data = [
            {"materia_codigo": "PROG1", "tipo": "Parcial", "numero_instancia": 1, "fecha": date(2026, 4, 15), "titulo": "Primer Parcial - Programacion I"},
            {"materia_codigo": "PROG1", "tipo": "Parcial", "numero_instancia": 2, "fecha": date(2026, 6, 20), "titulo": "Segundo Parcial - Programacion I"},
            {"materia_codigo": "PROG2", "tipo": "TP", "numero_instancia": 1, "fecha": date(2026, 5, 10), "titulo": "TP Integrador - Programacion II"},
            {"materia_codigo": "BD1", "tipo": "Parcial", "numero_instancia": 1, "fecha": date(2026, 4, 22), "titulo": "Primer Parcial - Base de Datos I"},
            {"materia_codigo": "MAT1", "tipo": "Coloquio", "numero_instancia": 1, "fecha": date(2026, 7, 5), "titulo": "Coloquio Final - Matematica I"},
            {"materia_codigo": "PROY1", "tipo": "TP", "numero_instancia": 1, "fecha": date(2026, 6, 1), "titulo": "Entrega Final - Gestion de Proyectos"},
        ]
        fechas_created = 0
        coh = tupad_cohortes[0]  # MAR-2025
        for fd in fechas_data:
            mat = materias.get(fd.pop("materia_codigo"))
            if mat is None:
                continue
            result = await session.execute(
                select(FechaEvaluacion).where(
                    FechaEvaluacion.tenant_id == tid,
                    FechaEvaluacion.materia_id == mat.id,
                    FechaEvaluacion.cohorte_id == coh.id,
                    FechaEvaluacion.tipo == fd["tipo"],
                    FechaEvaluacion.numero_instancia == fd["numero_instancia"],
                )
            )
            fe = result.scalar_one_or_none()
            if fe is None:
                fe = FechaEvaluacion(
                    tenant_id=tid,
                    materia_id=mat.id,
                    cohorte_id=coh.id,
                    **fd,
                )
                session.add(fe)
                fechas_created += 1
        if fechas_created > 0:
            await session.flush()
            print(f"  Created {fechas_created} fechas de evaluacion")

    await session.commit()
    print("\nDemo data seeded successfully.")


async def _main() -> None:
    """Standalone entry point."""
    print("Seeding demo data...")
    session_maker = get_session_maker()
    async with session_maker() as session:
        await seed_demo_data(session)


if __name__ == "__main__":
    asyncio.run(_main())
