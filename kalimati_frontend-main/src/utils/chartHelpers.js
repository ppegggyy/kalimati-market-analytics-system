export function getChartMargin(isMobile, isTablet) {
  if (isMobile) return { top: 8, right: 4, left: -8, bottom: 0 };
  if (isTablet) return { top: 10, right: 12, left: 0, bottom: 0 };
  return { top: 10, right: 30, left: 10, bottom: 0 };
}

export function getYAxisWidth(isMobile, isTablet) {
  if (isMobile) return 48;
  if (isTablet) return 64;
  return 80;
}

export function getAxisFontSize(isMobile, isTablet) {
  if (isMobile) return 10;
  if (isTablet) return 11;
  return 12;
}

export function getVolatilityChartMargin(isMobile, isTablet) {
  if (isMobile) return { top: 8, right: 4, left: -8, bottom: 72 };
  if (isTablet) return { top: 10, right: 12, left: 0, bottom: 88 };
  return { top: 10, right: 30, left: 10, bottom: 100 };
}

export function getVolatilityXAxisProps(isMobile, isTablet) {
  if (isMobile) {
    return { angle: -65, textAnchor: 'end', interval: 1, height: 88, fontSize: 9 };
  }
  if (isTablet) {
    return { angle: -50, textAnchor: 'end', interval: 0, height: 100, fontSize: 10 };
  }
  return { angle: -45, textAnchor: 'end', interval: 0, height: 120, fontSize: 12 };
}
