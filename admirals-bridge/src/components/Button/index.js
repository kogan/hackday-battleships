import styled from "styled-components";

const Button = styled.button`
  padding: 10px 16px;
  border: solid 1px #40a692;
  background-color: ${(props) => (props.active ? "#40a692" : "#1b2b28")};
  font-family: Roboto, Arial, sans-serif;
  font-size: 14px;
  font-weight: 500;
  font-stretch: normal;
  font-style: normal;
  line-height: 1.14;
  letter-spacing: 1.25px;
  text-align: center;
  color: #ffffff;
  text-transform: uppercase;

  &:hover,
  &:active,
  &:focus {
    background-color: #40a692;
  }

  & + & {
    margin-left: 16px;
  }
`;

export default Button;
