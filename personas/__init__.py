"""Persona assignment system for SpendSense."""

from personas.definitions import Persona, PERSONA_DEFINITIONS, PersonaRisk
from personas.assigner import PersonaAssigner
from personas.traces import DecisionTrace

__all__ = ['Persona', 'PERSONA_DEFINITIONS', 'PersonaAssigner', 'DecisionTrace', 'PersonaRisk']

