class Clinic:
    def __init__(self,
                 clinicId: int = 0,
                 clinicName: str = None,
                 clinicAddress: str = None,
                 clinicPostal: str = None,
                 clinicUnit: str = None,
                 clinicEmail: str = None,
                 clinicSubEmail: str = None,
                 clinicPhone: str = None,
                 clinicSubPhone: str = None) -> None:
        self._clinicId = clinicId
        self._clinicName = clinicName
        self._clinicAddress = clinicAddress
        self._clinicPostal = clinicPostal
        self._clinicUnit = clinicUnit
        self._clinicEmail = clinicEmail
        self._clinicSubEmail = clinicSubEmail
        self._clinicPhone = clinicPhone
        self._clinicSubPhone = clinicSubPhone

    def to_document(self) -> dict:
        return dict(
            _clinicName=self._clinicName,
            _clinicAddress=self._clinicAddress,
            _clinicPostal=self._clinicPostal,
            _clinicUnit=self._clinicUnit,
            _clinicEmail=self._clinicEmail,
            _clinicSubEmail=self._clinicSubEmail,
            _clinicPhone=self._clinicPhone,
            _clinicSubPhone=self._clinicSubPhone
        )

    @classmethod
    def from_document(cls, doc):
        return cls(
            clinicId=doc['_clinicId'],
            clinicName=doc['_clinicName'],
            clinicAddress=doc['_clinicAddress'],
            clinicPostal=doc['_clinicPostal'],
            clinicUnit=doc['_clinicUnit'],
            clinicEmail=doc['_clinicEmail'],
            clinicSubEmail=doc['_clinicSubEmail'],
            clinicPhone=doc['_clinicPhone'],
            clinicSubPhone=doc['_clinicSubPhone']
        )

    # Using property decorator
    # Getter method
    @property
    def clinicId(self):
        return self._clinicId

    @property
    def clinicName(self):
        return self._clinicName

    @property
    def clinicAddress(self):
        return self._clinicAddress

    @property
    def clinicPostal(self):
        return self._clinicPostal

    @property
    def clinicUnit(self):
        return self._clinicUnit

    @property
    def clinicEmail(self):
        return self._clinicEmail

    @property
    def clinicSubEmail(self):
        return self._clinicSubEmail

    @property
    def clinicPhone(self):
        return self._clinicPhone

    @property
    def clinicSubPhone(self):
        return self._clinicSubPhone