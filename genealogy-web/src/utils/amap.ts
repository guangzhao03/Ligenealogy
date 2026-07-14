import AMapLoader from '@amap/amap-jsapi-loader'

declare global {
  interface Window {
    _AMapSecurityConfig?: { securityJsCode: string }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    AMap?: any
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let loadPromise: Promise<any> | null = null

export function getAmapKey() {
  return (import.meta.env.VITE_AMAP_KEY as string | undefined)?.trim() || ''
}

export function getAmapSecurityCode() {
  return (import.meta.env.VITE_AMAP_SECURITY_CODE as string | undefined)?.trim() || ''
}

export function hasAmapKey() {
  return Boolean(getAmapKey())
}

/** 确保安全配置在任何 AMap 脚本请求前已写入 window */
export function ensureAmapSecurityConfig() {
  const securityCode = getAmapSecurityCode()
  if (securityCode) {
    window._AMapSecurityConfig = { securityJsCode: securityCode }
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function loadAmap(plugins: string[] = []): Promise<any> {
  const key = getAmapKey()
  if (!key) {
    throw new Error('未配置高德地图 Key（VITE_AMAP_KEY）')
  }

  ensureAmapSecurityConfig()

  if (!loadPromise) {
    loadPromise = AMapLoader.load({
      key,
      version: '2.0',
      plugins: [...new Set(['AMap.ToolBar', ...plugins])],
      AMapUI: undefined,
    }).catch((error: unknown) => {
      loadPromise = null
      throw error
    })
  } else if (plugins.length) {
    const AMap = await loadPromise
    await new Promise<void>((resolve, reject) => {
      try {
        AMap.plugin(plugins, () => resolve())
      } catch (error) {
        reject(error)
      }
    })
    return AMap
  }

  return loadPromise
}
