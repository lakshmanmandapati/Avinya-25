import React, { useEffect } from "react";

const ZapierEmbed = ({ zapId, title }) => {
  useEffect(() => {
    // Re-run Zapier embed script after component mounts
    if (window.Zapier && window.Zapier.init) {
      window.Zapier.init();
    }
  }, []);

  return (
    <div
      className="zapier-embed"
      data-zap-id={zapId}
      data-theme="light"
      data-zap-title={title}
    ></div>
  );
};

export default ZapierEmbed;
