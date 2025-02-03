export function DateToFormDisplay(
  date: Date,
): string {

  const iso =  date.toISOString();
  const day = iso.split("T")[0];
  const time = iso.split('T')[1].slice(0, 5);
  return day + " " + time;
}