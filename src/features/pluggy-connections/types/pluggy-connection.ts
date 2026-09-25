export interface PluggyConnection {
  item_id: string
  created_at: string
}

export interface PluggyConnectionsResponse {
  connections: PluggyConnection[]
}
