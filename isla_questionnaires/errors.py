class QuestionnaireError(ValueError):
    """Base exception for validation and state failures."""


class DefinitionError(QuestionnaireError):
    pass


class AnswerError(QuestionnaireError):
    pass


class IncompleteQuestionnaire(QuestionnaireError):
    pass


class ReviewRequired(QuestionnaireError):
    pass


class IntegrityError(QuestionnaireError):
    pass
