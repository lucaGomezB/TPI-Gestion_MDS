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
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session_maker
from app.core.security import hash_password
from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.models.aviso import Aviso
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.comunicacion import Comunicacion, LoteComunicacion
from app.models.evaluacion_coloquio import EvaluacionColoquio
from app.models.factura import Factura
from app.models.fecha_evaluacion import FechaEvaluacion
from app.models.grilla_salarial import GrupoMateria, SalarioBase, SalarioPlus
from app.models.guardia import Guardia
from app.models.hilo_mensaje import HiloMensaje
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.liquidacion import Liquidacion
from app.models.materia import Materia
from app.models.mensaje import Mensaje
from app.models.rol import Rol
from app.models.slot_encuentro import SlotEncuentro
from app.models.tarea import ComentarioTarea, Tarea
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol

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

    # ── Docente users ──────────────────────────────────────────────────
    docentes_data = [
        {"email": "profesor@tupad.edu.ar", "nombre": "Carlos", "apellidos": "Garcia", "rol": "PROFESOR"},
        {"email": "tutor@tupad.edu.ar", "nombre": "Maria", "apellidos": "Lopez", "rol": "TUTOR"},
        {"email": "coordinador@tupad.edu.ar", "nombre": "Jose", "apellidos": "Martinez", "rol": "COORDINADOR"},
        {"email": "nexo@tupad.edu.ar", "nombre": "Ana", "apellidos": "Fernandez", "rol": "NEXO"},
        {"email": "finanzas@tupad.edu.ar", "nombre": "Laura", "apellidos": "Rodriguez", "rol": "FINANZAS"},
    ]
    docentes_created = 0
    for dd in docentes_data:
        uh = Usuario.compute_email_hash(dd["email"])
        result = await session.execute(
            select(Usuario).where(Usuario.tenant_id == tid, Usuario.email_hash == uh)
        )
        docente = result.scalar_one_or_none()
        if docente is None:
            docente = Usuario(
                tenant_id=tid,
                email=dd["email"],
                email_hash=uh,
                nombre=dd["nombre"],
                apellidos=dd["apellidos"],
                password_hash=hash_password("password123"),
            )
            session.add(docente)
            await session.flush()
            print(f"  Created user: {dd['email']} ({dd['rol']})")
            docentes_created += 1

        # Assign role via UsuarioRol
        result = await session.execute(
            select(Rol).where(Rol.tenant_id == tid, Rol.nombre == dd["rol"])
        )
        rol = result.scalar_one_or_none()
        if rol is not None:
            result = await session.execute(
                select(UsuarioRol).where(
                    UsuarioRol.usuario_id == docente.id,
                    UsuarioRol.rol_id == rol.id,
                )
            )
            existing_ur = result.scalar_one_or_none()
            if existing_ur is None:
                ur = UsuarioRol(
                    usuario_id=docente.id,
                    rol_id=rol.id,
                    tenant_id=tid,
                )
                session.add(ur)
                print(f"    Assigned {dd['rol']} role to {dd['email']}")

    if docentes_created > 0:
        print(f"  Created {docentes_created} docente users")

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

    # ── Encuentros (slots + instancias) ────────────────────────────────
    result = await session.execute(
        select(Asignacion).where(Asignacion.tenant_id == tid).limit(6)
    )
    asigs = result.scalars().all()

    if asigs:
        # Slot 1: Clase Teorica Semanal (recurring)
        asig_a = asigs[0]
        result = await session.execute(
            select(SlotEncuentro).where(
                SlotEncuentro.tenant_id == tid,
                SlotEncuentro.materia_id == asig_a.materia_id,
                SlotEncuentro.titulo == "Clase Teorica Semanal",
            )
        )
        slot1 = result.scalar_one_or_none()
        if slot1 is None:
            slot1 = SlotEncuentro(
                tenant_id=tid,
                asignacion_id=asig_a.id,
                materia_id=asig_a.materia_id,
                titulo="Clase Teorica Semanal",
                hora=time(18, 0),
                dia_semana="Lunes",
                fecha_inicio=date(2026, 3, 9),
                cant_semanas=16,
                meet_url="https://meet.google.com/abc-defg-hij",
                vig_desde=date(2026, 3, 1),
                vig_hasta=date(2026, 7, 15),
            )
            session.add(slot1)
            await session.flush()
            print("  Created slot: Clase Teorica Semanal")

        # Slot 2: Practica Semanal (recurring)
        asig_b = asigs[1] if len(asigs) > 1 else asigs[0]
        result = await session.execute(
            select(SlotEncuentro).where(
                SlotEncuentro.tenant_id == tid,
                SlotEncuentro.materia_id == asig_b.materia_id,
                SlotEncuentro.titulo == "Practica Semanal",
            )
        )
        slot2 = result.scalar_one_or_none()
        if slot2 is None:
            slot2 = SlotEncuentro(
                tenant_id=tid,
                asignacion_id=asig_b.id,
                materia_id=asig_b.materia_id,
                titulo="Practica Semanal",
                hora=time(20, 0),
                dia_semana="Miercoles",
                fecha_inicio=date(2026, 3, 11),
                cant_semanas=14,
                meet_url="https://meet.google.com/xyz-uvwx-yz",
                vig_desde=date(2026, 3, 1),
                vig_hasta=date(2026, 7, 1),
            )
            session.add(slot2)
            await session.flush()
            print("  Created slot: Practica Semanal")

        # Instancias (some linked to slots, some standalone)
        instancias_data = [
            {"slot": "slot1", "fecha": date(2026, 3, 16), "hora": time(18, 0), "titulo": "Clase 1 - Introduccion", "comentario": "Presentacion de la materia"},
            {"slot": "slot1", "fecha": date(2026, 3, 23), "hora": time(18, 0), "titulo": "Clase 2 - Unidad 1", "comentario": "Conceptos fundamentales"},
            {"slot": "slot1", "fecha": date(2026, 4, 6), "hora": time(18, 0), "titulo": "Clase 3 - Unidad 2", "comentario": None},
            {"slot": "slot2", "fecha": date(2026, 3, 18), "hora": time(20, 0), "titulo": "Practica 1 - Ejercicios", "comentario": "Trabajo en grupos"},
            {"slot": None, "fecha": date(2026, 5, 15), "hora": time(18, 0), "titulo": "Consulta Extra - Pre-Parcial", "comentario": "Repaso general antes del parcial"},
            {"slot": None, "fecha": date(2026, 6, 25), "hora": time(18, 0), "titulo": "Recuperatorio", "comentario": "Instancia de recuperacion"},
        ]
        instancias_created = 0
        for idata in instancias_data:
            slot_ref = idata.pop("slot")
            if slot_ref == "slot1":
                slot_id = slot1.id
                mat_id = slot1.materia_id
            elif slot_ref == "slot2":
                slot_id = slot2.id
                mat_id = slot2.materia_id
            else:
                slot_id = None
                mat_id = asig_a.materia_id

            result = await session.execute(
                select(InstanciaEncuentro).where(
                    InstanciaEncuentro.tenant_id == tid,
                    InstanciaEncuentro.materia_id == mat_id,
                    InstanciaEncuentro.fecha == idata["fecha"],
                    InstanciaEncuentro.titulo == idata["titulo"],
                )
            )
            inst = result.scalar_one_or_none()
            if inst is None:
                inst = InstanciaEncuentro(
                    tenant_id=tid,
                    slot_id=slot_id,
                    materia_id=mat_id,
                    **idata,
                )
                session.add(inst)
                instancias_created += 1

    if instancias_created > 0:
        await session.flush()
        print(f"  Created {instancias_created} instancias de encuentro")

    # ═══════════════════════════════════════════════════════════════════
    # ── Resolve docentes for later sections ────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    uh = Usuario.compute_email_hash("profesor@tupad.edu.ar")
    result = await session.execute(
        select(Usuario).where(Usuario.tenant_id == tid, Usuario.email_hash == uh)
    )
    profesor = result.scalar_one()

    uh = Usuario.compute_email_hash("tutor@tupad.edu.ar")
    result = await session.execute(
        select(Usuario).where(Usuario.tenant_id == tid, Usuario.email_hash == uh)
    )
    tutor = result.scalar_one()

    uh = Usuario.compute_email_hash("coordinador@tupad.edu.ar")
    result = await session.execute(
        select(Usuario).where(Usuario.tenant_id == tid, Usuario.email_hash == uh)
    )
    coordinador = result.scalar_one()

    uh = Usuario.compute_email_hash("nexo@tupad.edu.ar")
    result = await session.execute(
        select(Usuario).where(Usuario.tenant_id == tid, Usuario.email_hash == uh)
    )
    nexo_user = result.scalar_one()

    # ═══════════════════════════════════════════════════════════════════
    # ── 1. Coloquios (3 items) ─────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    coloquios_data = [
        {
            "materia_codigo": "PROG1",
            "titulo": "Coloquio Final - Programacion I (Julio 2026)",
            "dias": [
                {"fecha": "2026-07-10", "cupos": 5, "reservados": 0},
                {"fecha": "2026-07-17", "cupos": 8, "reservados": 0},
            ],
        },
        {
            "materia_codigo": "BD1",
            "titulo": "Coloquio Final - Base de Datos I (Julio 2026)",
            "dias": [
                {"fecha": "2026-07-10", "cupos": 5, "reservados": 0},
                {"fecha": "2026-07-17", "cupos": 8, "reservados": 0},
            ],
        },
        {
            "materia_codigo": "MAT1",
            "titulo": "Coloquio Final - Matematica I (Julio 2026)",
            "dias": [
                {"fecha": "2026-07-10", "cupos": 5, "reservados": 0},
                {"fecha": "2026-07-17", "cupos": 8, "reservados": 0},
            ],
        },
    ]
    coloquios_created = 0
    for cd in coloquios_data:
        mat = materias[cd["materia_codigo"]]
        result = await session.execute(
            select(EvaluacionColoquio).where(
                EvaluacionColoquio.tenant_id == tid,
                EvaluacionColoquio.materia_id == mat.id,
                EvaluacionColoquio.titulo == cd["titulo"],
            )
        )
        ec = result.scalar_one_or_none()
        if ec is None:
            ec = EvaluacionColoquio(
                tenant_id=tid,
                materia_id=mat.id,
                titulo=cd["titulo"],
                dias=cd["dias"],
                creado_por=uid,
                activa=True,
                cohorte_id=tupad_cohortes[0].id,
            )
            session.add(ec)
            coloquios_created += 1
    if coloquios_created > 0:
        await session.flush()
        print(f"  Created {coloquios_created} coloquios")

    # ═══════════════════════════════════════════════════════════════════
    # ── 2. Guardias (3 items) ──────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    result = await session.execute(
        select(Asignacion).where(Asignacion.tenant_id == tid).limit(3)
    )
    asig_sample = result.scalars().all()

    guardias_data = [
        {"asignacion": asig_sample[0], "dia": "Lunes", "horario": "14:00-16:00"},
        {"asignacion": asig_sample[1] if len(asig_sample) > 1 else asig_sample[0], "dia": "Miercoles", "horario": "16:00-18:00"},
        {"asignacion": asig_sample[2] if len(asig_sample) > 2 else asig_sample[0], "dia": "Viernes", "horario": "10:00-12:00"},
    ]
    guardias_created = 0
    for gd in guardias_data:
        a = gd["asignacion"]
        result = await session.execute(
            select(Guardia).where(
                Guardia.tenant_id == tid,
                Guardia.asignacion_id == a.id,
                Guardia.dia == gd["dia"],
                Guardia.horario == gd["horario"],
            )
        )
        g = result.scalar_one_or_none()
        if g is None:
            g = Guardia(
                tenant_id=tid,
                asignacion_id=a.id,
                materia_id=a.materia_id,
                carrera_id=a.carrera_id,
                cohorte_id=a.cohorte_id,
                dia=gd["dia"],
                horario=gd["horario"],
                estado="Pendiente",
            )
            session.add(g)
            guardias_created += 1
    if guardias_created > 0:
        await session.flush()
        print(f"  Created {guardias_created} guardias")

    # ═══════════════════════════════════════════════════════════════════
    # ── 3. Avisos (4 items) ────────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    avisos_data = [
        {
            "alcance": "Global",
            "severidad": "Alta",
            "titulo": "Inicio de Cuatrimestre",
            "cuerpo": "El cuatrimestre comienza el 9 de Marzo de 2026. Verifiquen sus asignaciones en el sistema.",
            "inicio_en": datetime(2026, 3, 1, 0, 0, 0),
            "fin_en": datetime(2026, 3, 31, 23, 59, 59),
            "orden": 1,
            "requiere_ack": True,
            "rol_destino": None,
            "materia_codigo": None,
        },
        {
            "alcance": "PorRol",
            "severidad": "Media",
            "titulo": "Reunion de coordinacion",
            "cuerpo": "Reunion obligatoria de coordinadores el viernes 13 de Marzo a las 18:00 en la sala de reuniones virtual.",
            "inicio_en": datetime(2026, 3, 10, 0, 0, 0),
            "fin_en": datetime(2026, 3, 20, 23, 59, 59),
            "orden": 2,
            "requiere_ack": False,
            "rol_destino": "COORDINADOR",
            "materia_codigo": None,
        },
        {
            "alcance": "PorMateria",
            "severidad": "Baja",
            "titulo": "Cambio de horario",
            "cuerpo": "La clase teorica de PROG1 pasa de Lunes a Martes a partir de Abril.",
            "inicio_en": datetime(2026, 3, 25, 0, 0, 0),
            "fin_en": datetime(2026, 7, 15, 23, 59, 59),
            "orden": 3,
            "requiere_ack": False,
            "rol_destino": None,
            "materia_codigo": "PROG1",
        },
        {
            "alcance": "Global",
            "severidad": "Critico",
            "titulo": "Feriado nacional",
            "cuerpo": "Feriado nacional el 1 de Mayo. No hay actividades academicas.",
            "inicio_en": datetime(2026, 4, 28, 0, 0, 0),
            "fin_en": datetime(2027, 12, 31, 23, 59, 59),
            "orden": 0,
            "requiere_ack": False,
            "rol_destino": None,
            "materia_codigo": None,
        },
    ]
    avisos_created = 0
    for ad in avisos_data:
        mat_id = materias[ad.pop("materia_codigo")].id if ad["materia_codigo"] else None
        result = await session.execute(
            select(Aviso).where(
                Aviso.tenant_id == tid,
                Aviso.titulo == ad["titulo"],
                Aviso.alcance == ad["alcance"],
            )
        )
        av = result.scalar_one_or_none()
        if av is None:
            av = Aviso(
                tenant_id=tid,
                materia_id=mat_id,
                activo=True,
                **ad,
            )
            session.add(av)
            avisos_created += 1
    if avisos_created > 0:
        await session.flush()
        print(f"  Created {avisos_created} avisos")

    # ═══════════════════════════════════════════════════════════════════
    # ── 4. Comunicaciones (1 lote + 2 comunicaciones) ──────────────────
    # ═══════════════════════════════════════════════════════════════════
    prog1 = materias["PROG1"]
    lote_asunto = "Aviso importante - Parcial"
    result = await session.execute(
        select(LoteComunicacion).where(
            LoteComunicacion.tenant_id == tid,
            LoteComunicacion.materia_id == prog1.id,
            LoteComunicacion.asunto == lote_asunto,
        )
    )
    lote = result.scalar_one_or_none()
    if lote is None:
        lote = LoteComunicacion(
            tenant_id=tid,
            materia_id=prog1.id,
            enviado_por=uid,
            asunto=lote_asunto,
            total=2,
            enviados=2,
            fallidos=0,
            estado="Completado",
            preview_confirmado=True,
        )
        session.add(lote)
        await session.flush()
        print("  Created lote comunicacion")

    # Comunicacion 1
    result = await session.execute(
        select(Comunicacion).where(
            Comunicacion.tenant_id == tid,
            Comunicacion.lote_id == lote.id,
            Comunicacion.asunto == lote_asunto,
        )
    )
    coms_existing = result.scalars().all()
    if len(coms_existing) == 0:
        com1 = Comunicacion(
            tenant_id=tid,
            lote_id=lote.id,
            materia_id=prog1.id,
            enviado_por=uid,
            destinatario="alumno1@example.com",
            asunto=lote_asunto,
            cuerpo="Estimado alumno, le recordamos que el primer parcial de Programacion I sera el 15 de Abril. Estudie los modulos 1 al 4.",
            estado="Enviado",
        )
        session.add(com1)
        com2 = Comunicacion(
            tenant_id=tid,
            lote_id=lote.id,
            materia_id=prog1.id,
            enviado_por=uid,
            destinatario="alumno2@example.com",
            asunto=lote_asunto,
            cuerpo="Estimado alumno, le recordamos que el primer parcial de Programacion I sera el 15 de Abril. Estudie los modulos 1 al 4.",
            estado="Enviado",
        )
        session.add(com2)
        await session.flush()
        print("  Created 2 comunicaciones")

    # ═══════════════════════════════════════════════════════════════════
    # ── 5. Mensajes (2 hilos + 4 mensajes) ─────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    # Hilo 1: admin <-> profesor
    hilo1_asunto = "Consulta sobre PROG1"
    result = await session.execute(
        select(HiloMensaje).where(
            HiloMensaje.tenant_id == tid,
            HiloMensaje.asunto == hilo1_asunto,
        )
    )
    hilo1 = result.scalar_one_or_none()
    if hilo1 is None:
        hilo1 = HiloMensaje(
            tenant_id=tid,
            asunto=hilo1_asunto,
            participantes=[uid, profesor.id],
        )
        session.add(hilo1)
        await session.flush()
        print("  Created hilo: Consulta sobre PROG1")

    # Hilo 2: coordinador <-> admin
    hilo2_asunto = "Reporte de guardias"
    result = await session.execute(
        select(HiloMensaje).where(
            HiloMensaje.tenant_id == tid,
            HiloMensaje.asunto == hilo2_asunto,
        )
    )
    hilo2 = result.scalar_one_or_none()
    if hilo2 is None:
        hilo2 = HiloMensaje(
            tenant_id=tid,
            asunto=hilo2_asunto,
            participantes=[coordinador.id, uid],
        )
        session.add(hilo2)
        await session.flush()
        print("  Created hilo: Reporte de guardias")

    # Messages for Hilo 1
    mensajes_created = 0
    result = await session.execute(
        select(Mensaje).where(
            Mensaje.tenant_id == tid,
            Mensaje.hilo_id == hilo1.id,
        )
    )
    msgs_h1 = result.scalars().all()
    if len(msgs_h1) == 0:
        m1 = Mensaje(
            tenant_id=tid,
            hilo_id=hilo1.id,
            remitente_id=uid,
            destinatario_id=profesor.id,
            asunto=hilo1_asunto,
            cuerpo="Hola, como va la materia?",
            leido=True,
        )
        session.add(m1)
        m2 = Mensaje(
            tenant_id=tid,
            hilo_id=hilo1.id,
            remitente_id=profesor.id,
            destinatario_id=uid,
            asunto="Re: " + hilo1_asunto,
            cuerpo="Bien, avanzando con el primer parcial",
            leido=False,
        )
        session.add(m2)
        mensajes_created += 2

    # Messages for Hilo 2
    result = await session.execute(
        select(Mensaje).where(
            Mensaje.tenant_id == tid,
            Mensaje.hilo_id == hilo2.id,
        )
    )
    msgs_h2 = result.scalars().all()
    if len(msgs_h2) == 0:
        m3 = Mensaje(
            tenant_id=tid,
            hilo_id=hilo2.id,
            remitente_id=coordinador.id,
            destinatario_id=uid,
            asunto=hilo2_asunto,
            cuerpo="Adjunto el reporte de guardias de la semana.",
            leido=True,
        )
        session.add(m3)
        m4 = Mensaje(
            tenant_id=tid,
            hilo_id=hilo2.id,
            remitente_id=uid,
            destinatario_id=coordinador.id,
            asunto="Re: " + hilo2_asunto,
            cuerpo="Recibido, gracias.",
            leido=True,
        )
        session.add(m4)
        mensajes_created += 2
    if mensajes_created > 0:
        print(f"  Created {mensajes_created} mensajes")

    # ═══════════════════════════════════════════════════════════════════
    # ── 6. Tareas (3 items + 2 comentarios) ────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    tareas_data = [
        {
            "asignado_por": uid,
            "asignado_a": profesor.id,
            "descripcion": "Preparar material PROG1 - Modulos 1 al 4 para el primer cuatrimestre",
            "estado": "En progreso",
            "materia_codigo": "PROG1",
        },
        {
            "asignado_por": coordinador.id,
            "asignado_a": tutor.id,
            "descripcion": "Corregir TPs BD1 - Trabajos practicos pendientes de correccion",
            "estado": "Pendiente",
            "materia_codigo": "BD1",
        },
        {
            "asignado_por": uid,
            "asignado_a": coordinador.id,
            "descripcion": "Organizar coloquios Julio - Definir fechas, cupos y tribunales para coloquios de Julio 2026",
            "estado": "Resuelta",
            "materia_codigo": None,
        },
    ]
    tareas_created: list[Tarea] = []
    for td in tareas_data:
        mat_codigo = td.pop("materia_codigo")
        mat_id = materias[mat_codigo].id if mat_codigo else None
        result = await session.execute(
            select(Tarea).where(
                Tarea.tenant_id == tid,
                Tarea.asignado_por == td["asignado_por"],
                Tarea.asignado_a == td["asignado_a"],
                Tarea.descripcion == td["descripcion"],
            )
        )
        t = result.scalar_one_or_none()
        if t is None:
            t = Tarea(
                tenant_id=tid,
                materia_id=mat_id,
                **td,
            )
            session.add(t)
            tareas_created.append(t)
    if tareas_created:
        await session.flush()
        print(f"  Created {len(tareas_created)} tareas")

    # Comentarios on tareas
    comentarios_created = 0
    if len(tareas_created) >= 3:
        tarea1 = tareas_created[0]
        tarea3 = tareas_created[2]

        # Comment on Tarea 1
        result = await session.execute(
            select(ComentarioTarea).where(
                ComentarioTarea.tenant_id == tid,
                ComentarioTarea.tarea_id == tarea1.id,
                ComentarioTarea.autor_id == profesor.id,
            )
        )
        ct1 = result.scalar_one_or_none()
        if ct1 is None:
            ct1 = ComentarioTarea(
                tenant_id=tid,
                tarea_id=tarea1.id,
                autor_id=profesor.id,
                texto="Ya tengo los primeros 3 modulos listos",
            )
            session.add(ct1)
            comentarios_created += 1

        # Comment on Tarea 3
        result = await session.execute(
            select(ComentarioTarea).where(
                ComentarioTarea.tenant_id == tid,
                ComentarioTarea.tarea_id == tarea3.id,
                ComentarioTarea.autor_id == uid,
            )
        )
        ct3 = result.scalar_one_or_none()
        if ct3 is None:
            ct3 = ComentarioTarea(
                tenant_id=tid,
                tarea_id=tarea3.id,
                autor_id=uid,
                texto="Listo, cerramos esta",
            )
            session.add(ct3)
            comentarios_created += 1
    if comentarios_created > 0:
        print(f"  Created {comentarios_created} comentarios de tarea")

    # ═══════════════════════════════════════════════════════════════════
    # ── 7. Audit Log (5 entries) ───────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    audit_entries = [
        {
            "accion": "USUARIO_CREADO",
            "actor_id": uid,
            "detalle": {"email": "profesor@tupad.edu.ar"},
            "filas_afectadas": 1,
            "ip": "127.0.0.1",
            "user_agent": "SeedScript/1.0",
        },
        {
            "accion": "MATERIA_CREADA",
            "actor_id": uid,
            "detalle": {"codigo": "PROG1"},
            "filas_afectadas": 1,
            "ip": "127.0.0.1",
            "user_agent": "SeedScript/1.0",
            "materia_id": materias["PROG1"].id,
        },
        {
            "accion": "ASIGNACION_CREADA",
            "actor_id": uid,
            "detalle": {"rol": "COORDINADOR"},
            "filas_afectadas": 24,
            "ip": "127.0.0.1",
            "user_agent": "SeedScript/1.0",
        },
        {
            "accion": "LOGIN_EXITOSO",
            "actor_id": uid,
            "detalle": {},
            "filas_afectadas": 0,
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
        },
        {
            "accion": "LOGIN_EXITOSO",
            "actor_id": profesor.id,
            "detalle": {},
            "filas_afectadas": 0,
            "ip": "192.168.1.2",
            "user_agent": "Mozilla/5.0",
        },
    ]
    audit_created = 0
    for ae in audit_entries:
        mat_id = ae.pop("materia_id", None)
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.tenant_id == tid,
                AuditLog.accion == ae["accion"],
                AuditLog.actor_id == ae["actor_id"],
            )
        )
        existing = result.scalars().all()
        # Only create if no entry with this accion+actor combination
        if len(existing) == 0:
            al = AuditLog(
                tenant_id=tid,
                materia_id=mat_id,
                **ae,
            )
            session.add(al)
            audit_created += 1
    if audit_created > 0:
        print(f"  Created {audit_created} audit log entries")

    # ═══════════════════════════════════════════════════════════════════
    # ── 8. Liquidaciones (4 items) ─────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    coh_mar2025 = cohortes["TUPAD/MAR-2025"]
    periodo = "2026-06"
    liquidaciones_data = [
        {
            "usuario_id": uid,
            "rol": "COORDINADOR",
            "comisiones": [],
            "monto_base": 150000.00,
            "monto_plus": 0.00,
            "total": 150000.00,
            "es_nexo": False,
            "estado": "Abierta",
        },
        {
            "usuario_id": profesor.id,
            "rol": "PROFESOR",
            "comisiones": ["A", "B"],
            "monto_base": 150000.00,
            "monto_plus": 20000.00,
            "total": 170000.00,
            "es_nexo": False,
            "estado": "Abierta",
        },
        {
            "usuario_id": tutor.id,
            "rol": "TUTOR",
            "comisiones": ["A"],
            "monto_base": 150000.00,
            "monto_plus": 20000.00,
            "total": 170000.00,
            "es_nexo": False,
            "estado": "Cerrada",
            "cerrada_at": datetime.now(),
        },
        {
            "usuario_id": nexo_user.id,
            "rol": "NEXO",
            "comisiones": [],
            "monto_base": 50000.00,
            "monto_plus": 0.00,
            "total": 50000.00,
            "es_nexo": True,
            "estado": "Abierta",
        },
    ]
    liquidaciones_created = 0
    for ld in liquidaciones_data:
        cerrada_at = ld.pop("cerrada_at", None)
        result = await session.execute(
            select(Liquidacion).where(
                Liquidacion.tenant_id == tid,
                Liquidacion.cohorte_id == coh_mar2025.id,
                Liquidacion.usuario_id == ld["usuario_id"],
                Liquidacion.periodo == periodo,
            )
        )
        liq = result.scalar_one_or_none()
        if liq is None:
            liq = Liquidacion(
                tenant_id=tid,
                cohorte_id=coh_mar2025.id,
                periodo=periodo,
                excluido_por_factura=False,
                cerrada_at=cerrada_at,
                **ld,
            )
            session.add(liq)
            liquidaciones_created += 1
    if liquidaciones_created > 0:
        await session.flush()
        print(f"  Created {liquidaciones_created} liquidaciones")

    # ═══════════════════════════════════════════════════════════════════
    # ── 9. Facturas (2 items) ──────────────────────────────────────────
    # ═══════════════════════════════════════════════════════════════════
    # Ensure profesor is flagged as facturador
    if not profesor.facturador:
        profesor.facturador = True
        session.add(profesor)

    facturas_data = [
        {
            "periodo": "2026-05",
            "detalle": "Factura Mayo 2026",
            "referencia_archivo": "factura_mayo_2026_profesor.pdf",
            "tamano_kb": 125.5,
            "estado": "Pendiente",
        },
        {
            "periodo": "2026-04",
            "detalle": "Factura Abril 2026",
            "referencia_archivo": "factura_abril_2026_profesor.pdf",
            "tamano_kb": 110.0,
            "estado": "Abonada",
            "abonada_at": datetime.now(),
        },
    ]
    facturas_created = 0
    for fd in facturas_data:
        abonada_at = fd.pop("abonada_at", None)
        result = await session.execute(
            select(Factura).where(
                Factura.tenant_id == tid,
                Factura.usuario_id == profesor.id,
                Factura.periodo == fd["periodo"],
            )
        )
        fac = result.scalar_one_or_none()
        if fac is None:
            fac = Factura(
                tenant_id=tid,
                usuario_id=profesor.id,
                abonada_at=abonada_at,
                **fd,
            )
            session.add(fac)
            facturas_created += 1
    if facturas_created > 0:
        print(f"  Created {facturas_created} facturas")

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
