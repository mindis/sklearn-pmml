import pandas as pd

class Feature(object):
    INVALID_TREATMENT_AS_IS = 'asIs'

    def __init__(self, name, namespace='', invalid_value_treatment=INVALID_TREATMENT_AS_IS):
        self._name = name
        self._namespace = namespace
        self._invalid_value_treatment = invalid_value_treatment

    @property
    def name(self):
        return self._name

    @property
    def namespace(self):
        return self._namespace

    @property
    def full_name(self):
        if self._namespace:
            return '{}::{}'.format(self._namespace, self.name)
        else:
            return self.name

    @property
    def invalid_value_treatment(self):
        return self._invalid_value_treatment

    @property
    def optype(self):
        raise NotImplementedError()

    @property
    def data_type(self):
        raise NotImplementedError()

    def from_number(self, value):
        raise NotImplementedError()

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}::{}".format(self.name, self.__class__.__name__)


class NumericFeature(Feature):
    @property
    def optype(self):
        return "continuous"

    def from_number(self, value):
        return float(value)


class RealNumericFeature(NumericFeature):
    @property
    def data_type(self):
        return "double"


class IntegerNumericFeature(NumericFeature):
    def from_number(self, value):
        return int(value)

    @property
    def data_type(self):
        return "integer"


class CategoricalFeature(Feature):
    """
    Represents a categorical feature. Categorical features are defined with optype 'categorical' and the corresponding
    dataType. The corresponding derived field will have a double data type and will be defined as a MapValues PMML
    element.
    """
    def __init__(self, name, value_list, namespace='', invalid_value_treatment=Feature.INVALID_TREATMENT_AS_IS):
        super(CategoricalFeature, self).__init__(name, namespace, invalid_value_treatment)
        self.value_list = value_list

    @property
    def optype(self):
        return "categorical"

    def from_number(self, value):
        assert value >= 0, 'Negative numbers can not be used as categorical indexes'
        assert value < len(self.value_list), 'Unknown category index {}'.format(value)
        return self.value_list[value]


class IntegerCategoricalFeature(CategoricalFeature):
    @property
    def data_type(self):
        return "integer"


class StringCategoricalFeature(CategoricalFeature):
    @property
    def data_type(self):
        return "string"


class DerivedFeature(NumericFeature):
    """
    This class represents a derived feature constructed from previously defined features.
    The transformation parameter defines the recipe for creating a feature, and will be inserted into pmml.DerivedField
    element for this feature.
    Note, that the transformation only allows references to the already declare fields.

    For convenience, one can also pass the function that performs the transformation on the input data frame.
    """

    def __init__(self, feature, transformation, function=None):
        """
        Construct a derived feature.
        :param feature: declaration of feature (name, data_type and optype)
        :param transformation: definition of DerivedField content
        :param function: transformation function
        """
        super(DerivedFeature, self).__init__(
            name=feature.name,
            namespace=feature.namespace,
            invalid_value_treatment=feature.invalid_value_treatment
        )
        assert isinstance(feature, NumericFeature), 'All derived features must be declared as NumericFeatures'
        self.feature = feature
        self.transformation = transformation
        self.function = function


    def from_number(self, value):
        return self.feature.from_number(value)

    def data_type(self):
        return self.feature.data_type

    def optype(self):
        return self.feature.optype

    def apply(self, df):
        """
        Calculate derived feature's values based on the values in the input data frame.
        Note that the input data frame will not be affected by the transformation.
        :param df: input data frame
        :return: array with results
        """
        assert self.function is not None, 'Function was not provided'
        assert isinstance(df, pd.DataFrame), 'Input should be a data frame'
        return self.function(df.copy(deep=False))