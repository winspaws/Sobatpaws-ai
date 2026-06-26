class PawniaError(Exception): pass
class PawniaAPIError(PawniaError): pass
class PawniaAuthError(PawniaError): pass
class PawniaNotFoundError(PawniaError): pass
