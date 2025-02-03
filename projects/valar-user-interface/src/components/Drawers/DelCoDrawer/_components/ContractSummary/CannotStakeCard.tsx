import { cn } from "@/lib/shadcn-utils";
import { Stakable } from "@/utils/staking-utils";

const CannotStakeCard: React.FC<{ stakable: Stakable | undefined; className?: string }> = ({ stakable, className }) => {

  if (!stakable) return;

  return (
    <div
      className={cn("h-min w-auto rounded-lg bg-gradient-to-br from-gradient-light to-gradient-dark p-3", className)}
    >
      <h1 className="my-1 font-bold text-base">You cannot currently select this node runner because:</h1>
      <ul className="mt-2 list-inside list-disc space-y-2 text-sm text-text-tertiary">
        {stakable.reasons.map((reason, index) => (
          <li key={index}>{reason}</li>
        ))}
      </ul>
    </div>
  );
};

export default CannotStakeCard;