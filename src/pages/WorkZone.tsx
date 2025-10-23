import React from 'react';
import ImageUpLoad from './../components/ImageUpLoad';
import ResFromServer from './../components/ResFromServer';
import Arrow from './../components/Arrow';

const WorkZone: React.FC = () => {
  return (
    <div className="workZoneMain">
        <div className="workZoneInfo">
            AI-ассистент VisionX поможет Вам обнаружить глаукому на снимке глазного дна
        </div>
        <div className="workZone">
        <ImageUpLoad />
        <Arrow />
        <ResFromServer />
        </div>
    </div>
  );
}

export default WorkZone;
