import React from 'react';
import styled from 'styled-components';

const SpinnerContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  position: relative;
`;

const TractorAnimationWrapper = styled.div`
  width: 180px;
  height: 130px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(0 0 15px rgba(16, 185, 129, 0.3));
`;

const LoadingText = styled.p`
  color: var(--dash-emerald, #10b981);
  font-family: 'Orbitron', monospace;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 0;
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
`;

const LoadingSpinner = ({ text = 'Cultivating Intelligence...' }) => {
  return (
    <SpinnerContainer>
      <TractorAnimationWrapper>
        <dotlottie-player
          src="/animations/soil cultivating.lottie"
          background="transparent"
          speed="1"
          style={{ width: '100%', height: '100%' }}
          loop
          autoplay
        />
      </TractorAnimationWrapper>
      <LoadingText>{text}</LoadingText>
    </SpinnerContainer>
  );
};

export default LoadingSpinner;
