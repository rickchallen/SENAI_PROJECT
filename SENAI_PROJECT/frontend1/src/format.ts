const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})

const dateFormatter = new Intl.DateTimeFormat('pt-BR', {
  dateStyle: 'short',
  timeStyle: 'short',
  timeZone: 'America/Recife',
})

export function money(value: number) {
  return currencyFormatter.format(value)
}

export function localDate(value: string) {
  return dateFormatter.format(new Date(value))
}

export function dateTimeInputDefault() {
  const date = new Date(Date.now() + 24 * 60 * 60 * 1000)
  const formatter = new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'America/Recife',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
  return formatter.format(date).replace(' ', 'T')
}

export function brasiliaDateTime(value: string) {
  return `${value}-03:00`
}
