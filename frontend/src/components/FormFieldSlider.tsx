import React from 'react';
import { FormGroup, FormHelperText, Slider, SliderOnChangeEvent } from '@patternfly/react-core';

interface FormFieldProps {
  name: string;
  state: {
    value: number;
  };
  handleChange: (value: number) => void;
  handleBlur: () => void;
}

interface FormProps {
  Field: React.ComponentType<{
    name: string;
    children: (field: FormFieldProps) => React.ReactNode;
  }>;
}

interface FormFieldSliderProps {
  form: FormProps;
  name: string;
  label: string;
  helperText: string;
  min: number;
  max: number;
  step: number;
  handleSliderChange: (
    event: SliderOnChangeEvent,
    field: FormFieldProps,
    sliderValue: number,
    inputValue: number | undefined,
    range: { min: number; max: number; step: number },
    setLocalInputValue?: React.Dispatch<React.SetStateAction<number>>
  ) => void;
}

const FormFieldSlider: React.FC<FormFieldSliderProps> = ({
  form,
  name,
  label,
  helperText,
  min,
  max,
  step,
  handleSliderChange,
}) => (
  <form.Field name={name}>
    {(field: FormFieldProps) => (
      <FormGroup
        label={label}
        fieldId={name}
        className="wide-input-slider"
        style={{ marginBottom: 24, marginLeft: 15 }}
      >
        <FormHelperText>{helperText}</FormHelperText>
        <div style={{ maxWidth: 1050 }}>
          <Slider
            value={field.state.value}
            min={min}
            max={max}
            step={step}
            isInputVisible
            inputValue={field.state.value}
            onChange={(event, value, inputValue, setLocalInputValue) =>
              handleSliderChange(
                event,
                field,
                value,
                inputValue,
                { min, max, step },
                setLocalInputValue
              )
            }
            aria-label={label}
          />
        </div>
      </FormGroup>
    )}
  </form.Field>
);

export default FormFieldSlider;
